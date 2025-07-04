#!/usr/local/bin/python
# -*- coding: utf-8 -*-

# sempre adicionar utf-8 por que? porque escrevemos em "portugues"!!!

__author__ = 'casimirdes'

"""
data: 14/09/16
autor: matheusjm
 baseado no terminal serial do arduino, faremos algo parecido e utlizando
 a biblioteca tkinter para criacao do app

requisitos:
 pip install pyserial
"""

from tkinter import *
# place (x=inicial, y=inicial, width=largura, height=altura)
import tkinter.ttk as ttk

from threading import Timer
import threading as th
import time
# import thread #???????????????????????????????
from sys import argv

# pip3 install pyserial
import serial
import serial.tools.list_ports

# from time import sleep

print("INICIAL DO APP...")

# mod para envio de pacote fixo para o outro dispositivo
TX_SIZEFIXED = False
SIZE_MAX_UARTRX = 256
print("SIZE_MAX_UARTRX =", SIZE_MAX_UARTRX)

# manipula utf-8 rx
salve_byte = 0
flag_byte = False

rx_thread = th.Thread()  # novo
# ======================================================================================================
# ======================================================================================================
# VARIAVEIS GLOBAIS
TAXA = 76800
PORTA = "COM8"
UART_OK = False  # flag que indica se a conexao foi realizada ou nao

sms1 = "Dipositivo não conectado!"
sms2 = "Dispositivo conectado!"

BYTES_TX = 0
BYTES_RX = 0
# ======================================================================================================
# ======================================================================================================


##################################################################################
##################################################################################
##################################################################################
"""                  DEFINIÇOES TKINTER DO PROGRAMA                            """
"""                  INTERFACE GRÁFICA DO PROGRAMA                             """

root = Tk()
root.tk.call('encoding', 'system', 'utf-8')
root.title('MONITOR SERIAL PY3')
# root.resizable(width=FALSE, height=FALSE)
# root.geometry('500x500')
root.minsize(400, 570)
# root.maxsize(500,560)
# root.wm_iconbitmap('imagens\chip.ico')

# metodos de geometria dos objetos no form temos grid(), pack() e place()


# SEQUENCIA VAI DE BAIXO PARA CIMA!!!!!!
# DEVISO O ESQUEMA DO METODO DE GEOMETRIA PACK()


# LINHA DE CONTAGEM DOS BYTES ENVIADOS E RECEBIDOS
# -------------------------------------------------------------------------------------------
st_bytes_tx = StringVar()
st_bytes_rx = StringVar()

frame_bytes = Frame(root, relief=RIDGE, bg='#99dd99')  # , width=350, height=20)
frame_bytes.pack(side=BOTTOM, anchor=W, expand=NO, fill=BOTH)

Label(frame_bytes, text="NÚMERO DE BYTES:", bg='#99dd99').pack(side=LEFT, anchor=W)

Label(frame_bytes, textvariable=st_bytes_rx, bg='#99dd99').pack(side=LEFT, anchor=W, padx=5)
Label(frame_bytes, textvariable=st_bytes_tx, bg='#99dd99').pack(side=LEFT, anchor=W, padx=5)

st_bytes_rx.set("RX (%u)" % BYTES_RX)
st_bytes_tx.set("TX (%u)" % BYTES_TX)
# -------------------------------------------------------------------------------------------


# LINHA DE REGISTRO DOS DADOS RECEBIDOS, TERMINAL...
# -------------------------------------------------------------------------------------------
frame_txt_terminal = Frame(root, bg="green", relief=RIDGE, width=100, height=20)
frame_txt_terminal.pack(side=BOTTOM, anchor=W, expand=YES, fill=BOTH)

textbox = Text(frame_txt_terminal, font='{Consolas} 11')
textbox.pack(side=LEFT, expand=YES, fill=BOTH)
textbox.insert(INSERT, "Mensagens do terminal...\n")

scrollbar = Scrollbar(frame_txt_terminal, orient=VERTICAL)
scrollbar.pack(side=RIGHT, fill=Y)

textbox.configure(yscrollcommand=scrollbar.set)

scrollbar.config(command=textbox.yview)

Label(root, text="TERMINAL SERIAL", font='{Arial} 12', bg="#33aa66").pack(side=BOTTOM, fill=BOTH)
# -------------------------------------------------------------------------------------------


# LINHA DE ENVIO DE BYTES (CHAR, BYTE, STRING....)
# -------------------------------------------------------------------------------------------
frame_send = Frame(root, bg="green", relief=RIDGE, width=220, height=20)
frame_send.pack(side=BOTTOM, anchor=W, expand=NO, fill=BOTH)

send_entry = Entry(frame_send, width=50, borderwidth=4)  # width=tamanho de caracteres...
send_entry.pack(side=LEFT, anchor=W, expand=YES, fill=X)
send_entry.insert(END, "")

bt_send = Button(frame_send, text=" ENVIAR ", bg='#22dd99', font='blod')
bt_send.pack(side=LEFT, anchor=W)
# -------------------------------------------------------------------------------------------


# LINHA DE STATUS E CONEXAO COM A PORTA SERIAL
# -------------------------------------------------------------------------------------------
frame_status = Frame(root, bg="#99dd44", relief=RIDGE, width=220, height=30)
frame_status.pack(side=BOTTOM, anchor=W, expand=NO, fill=BOTH)

bt_connect = Button(frame_status, text="CONECTAR", font='blod')
bt_connect.pack(side=LEFT, anchor=W, padx=1, pady=1)
bt_connect.configure(bg="red")

st_status = StringVar()
Label(frame_status, textvariable=st_status, bg='#99dd44', font=11).pack(side=LEFT, anchor=W, padx=5)

st_status.set(sms1)
# -------------------------------------------------------------------------------------------


# LINHA DE CONFIGURACAO DA PORTA DE SERIAL
# -------------------------------------------------------------------------------------------
frame_config = Frame(root, bg="#9999dd", relief=RIDGE, width=220, height=30)
frame_config.pack(side=BOTTOM, anchor=W, expand=NO, fill=BOTH)

# dados da porta:
Label(frame_config, text="PORTA COM: ", bg="#9999dd", font=10).pack(side=LEFT, anchor=W)

port_entry = Entry(frame_config, width=4, font=10)  # width=tamanho de caracteres...
port_entry.pack(side=LEFT, anchor=E)
port_entry.insert(END, "24")

# dados de volocidade de conexao, baud rate(taxa) bps
Label(frame_config, text="BAUD RATE: ", bg="#9999dd", font=10).pack(side=LEFT)

lista_taxa = ["600", "1200", "2400", "4800", "9600", "19200", "38400", "57600", "76800", "115200", "128000", "230400",
              "460800", "576000", "921600"]
combo_taxa = ttk.Combobox(frame_config, values=lista_taxa, state='readonly', width=6, font=10)
combo_taxa.pack(side=LEFT)
combo_taxa.set(value=lista_taxa[6])

auto_down = IntVar()
Checkbutton(frame_config, text="Auto-rolagem", width=15, variable=auto_down, onvalue=1,
            offvalue=0, bg="#9999dd", font=10).pack(side=RIGHT)


# -------------------------------------------------------------------------------------------


# ======================================================================================================
# ======================================================================================================
# FUNCOES DO APP


# uma vez definido uma variavel ou objeto ou entao tudo é objeto logo entao uma vez definido com global
# em uma so funcao para as demais funcoes essa variavel ja sera dita como global....

"""
# FUNÇAO PRINCIPAL QUE MONITORA E RECEBE TUDO O QUE VIER PELA SERIAL
def RX_DATA():
    global BYTES_RX, salve_byte, flag_byte

    if serial_port.isOpen():
        while True:
            if serial_port.inWaiting() > 0:  # numero de bytes que temos no buffer de entrada...
                # ================================================================================================
                # ================================================================================================
                '''
                # retorna um char tipo char mesmo tipo tabela anscii
                byte_rx = (serial_port.read())  # ler uma vez somente senao ja puxa outros bytes

                if byte_rx[0] > 126:  # considerando "utf-8"
                    if flag_byte is False:
                        salve_byte = byte_rx
                        flag_byte = True
                    else:
                        salve_byte += byte_rx
                        try:
                            textbox.insert(END, salve_byte.decode(encoding="utf-8"))
                        except UnicodeDecodeError:
                            print("erro UnicodeDecodeError")
                        flag_byte = False
                else:
                    textbox.insert(END, byte_rx)
                '''
                x = serial_port.inWaiting()
                print("x = ", x)
                byte_rx = serial_port.read()
                message = byte_rx.decode(encoding="utf-8")
                textbox.insert(END, message)

                if auto_down.get():  # retona um int...
                    textbox.yview(END)  # configura o auto-relagem!!!!!

                BYTES_RX += 1  # teste de contagem numero de bytes
            # caso inWaiting() seja zero, sai fora do while true
            else:
                break  # sai fora do while true
            # ================================================================================================
            # ================================================================================================
        serial_port.flushInput()  # flush input buffer, discarding all its contents
        serial_port.flushOutput()  # flush output buffer, aborting current output
    st_bytes_rx.set("RX (%u)" % BYTES_RX)

    try:
        root.after(100, RX_DATA)  # 100ms
    except:
        print("erro timer")
"""


def RX_DATA_th():
    global BYTES_RX
    while UART_OK:
        try:
            if serial_port.isOpen():
                while UART_OK:
                    while not serial_port.inWaiting() and UART_OK is True:
                        time.sleep(0.05)  # isso implica na velocidade da serial...
                        #print("x")
                    cont = 0
                    message = bytes()
                    while True:
                        bytesToRead = serial_port.inWaiting()
                        result = serial_port.read(bytesToRead)
                        #print("bytesToRead", bytesToRead)
                        cont+=bytesToRead
                        message+=result
                        """
                        if result:
                            textbox.insert(END, result)
                            #print("cont", cont)
                        else:
                            break
                        """
                        if not result:
                            break
                        time.sleep(0.05)
                    print("len message", len(message))
                    textbox.insert(END, message.decode(encoding="utf-8"))
                    if auto_down.get():  # retona um int...
                        textbox.yview(END)  # configura o auto-relagem!!!!!

                    BYTES_RX += cont  # teste de contagem numero de bytes
                    #time.sleep(0.001)


                    """
                    if serial_port.inWaiting() > 0:  # numero de bytes que temos no buffer de entrada...
                        #================================================================================================
                        #================================================================================================
                        # retorna um char tipo char mesmo tipo tabela anscii
                        byte_rx = (serial_port.read()) # ler uma vez somente senao ja puxa outros bytes
                        textbox.insert(END, byte_rx)
    
                        if auto_down.get():  # retona um int...
                            textbox.yview(END)  # configura o auto-relagem!!!!!
    
                        BYTES_RX +=1 # teste de contagem numero de bytes
                    # caso inWaiting() seja zero, sai fora do while true
                    else:
                        break  # sai fora do while true
                    #================================================================================================
                    #================================================================================================
                    """
                # serial_port.flushInput() #flush input buffer, discarding all its contents
                # serial_port.flushOutput()#flush output buffer, aborting current output

            st_bytes_rx.set("RX (%u)" % BYTES_RX)
        except:
            print("erro except... nao tratado")  # entra aqui quando fecha e esta a thread aberta e serial em andamento...
    if UART_OK is False:
        serial_port.close()
        print("fecha porta serial")
    print("saio do thread RX_DATA_th")





def chama_serial():
    global TAXA, PORTA, UART_OK
    global serial_port
    global rx_thread  # novo

    PORTA = "COM" + port_entry.get()
    TAXA = combo_taxa.get()

    conexao = "Porta = %s, Taxa = %s\n\n" % (PORTA, TAXA)  # cria string para imprimir no terminal...

    try:
        serial_port = serial.Serial(PORTA, TAXA)
        serial_port.flushInput()  # flush input buffer, discarding all its contents
        serial_port.flushOutput()  # flush output buffer, aborting current output

        UART_OK = True  # flag passa para verdadeiro

        textbox.insert(END, "\nCONEXAO DA PORTA SERIAL ESTABELECIDA\n")
        textbox.insert(END, conexao)
        textbox.yview(END)

        bt_connect.configure(bg="green")
        bt_connect.configure(state=DISABLED)

        st_status.set(sms2)

        # "segredo" esta aqui, funcao RX_DATA fica sendo atualizada a cada x ms, podem ser exploradas outras formas
        # como funçoes multithreads....
        # quanto mais rapida a taxa do serial menor deve ser o tempo de atualizacao (os ms)
        # para 50ms funciona ok para velocidades até 115200bps...
        ####root.after(50, RX_DATA)  # ja ativa a funcao de recepcao dos bytes via um "timer" em x tempo


        print("iniciando a thread")
        rx_thread = th.Thread(target=RX_DATA_th)  # chama a funcao real_time_adc para thread
        #ws_thread = th.Thread(target=websocket_thread, args=("websocket thread",))  # chama a funcao real_time_adc para thread
        rx_thread.start()

    except:
        textbox.insert(END, "\nERRO DE CONEXAO DE PORTA SERIAL \n")
        port_entry.delete(0, END)
        port_entry.insert(END, "1")
        textbox.yview(END)
        UART_OK = False


def envia_serial():
    global BYTES_TX
    data = send_entry.get()
    if len(data) > 0:
        if UART_OK is True:
            if serial_port.isOpen():
                if TX_SIZEFIXED:
                    pack = bytearray(SIZE_MAX_UARTRX)
                    dataB = data.encode('utf-8')
                    for i, d in enumerate(dataB):
                        pack[i] = d
                    serial_port.write(pack)
                    sss = "\n==============================================================\n"
                    sss += ("PC ENVIA: %s\n" % data)
                    sss += "==============================================================\n"
                    textbox.insert(END, sss)
                else:
                    serial_port.write(data.encode('utf-8'))
                    textbox.insert(END, "\n==============================================================\n")
                    textbox.insert(END, ("\nPC ENVIA: %s\n" % data))
                    textbox.insert(END, "\n==============================================================\n")
                if auto_down.get():
                    textbox.yview(END)
                BYTES_TX += len(data)
                st_bytes_tx.set("TX (%u)" % BYTES_TX)
                time.sleep(0.01)
        send_entry.delete(0, END)
    else:
        print("data = ", data)


def envia_enter(event):
    """ evento do click do botao ENTER do teclado imprime o selecionado..."""
    # print("event tecla...")
    # valido para tecla ENTER
    if event.keysym == 'Return':
        print("TECLA ENTER PRESSIONADA!!!")
        envia_serial()
    # print("saindo evento tecla")


# ======================================================================================================
# ======================================================================================================


# ======================================================================================================
# ======================================================================================================
# CONFIGURACOES DOS OBJETOS POS CRIACAO DAS FUNCOES

bt_connect.configure(command=chama_serial)

bt_send.configure(command=envia_serial)

send_entry.bind("<KeyRelease>", envia_enter)
# ======================================================================================================
# ======================================================================================================


# ======================================================================================================
# verifica a existencia ou nao de portas COM no computador....
# isso nao funciona no LINUX... acho eu...
ports = list(serial.tools.list_ports.comports())
for p in ports:
    try:
        print(p)
        textbox.insert(END, p)
    except:
        textbox.insert(END, "NAO FORAM ENCONTRADAS PORTAS <COM>\n PARA COMUNICAÇÃO\n")

if len(ports) == 0:
    textbox.insert(END, "NAO FORAM ENCONTRADAS PORTAS <COM> PARA COMUNICAÇÃO\n")
# ======================================================================================================


print("INICIAL LOOP DO TKINTER")

root.mainloop()

# verifica  porta serial e/ou se os outros timer foram ativados para desativar......
if UART_OK == True:
    UART_OK = False
    time.sleep(5)
    """
    if rx_thread.is_alive():
        rx_thread.do_run = False
        rx_thread.join()
    """
    # serial_port.close()
    print("PORTA SERIAL FECHADA")
    print("NUMERO TOTAL DE BYTES RECEBIDOS = %d" % BYTES_RX)
    print("NUMERO TOTAL DE BYTES TRANSMITIDOS = %d" % BYTES_TX)

print("APP FINAIZADO NO BOTAO FECHAR")
