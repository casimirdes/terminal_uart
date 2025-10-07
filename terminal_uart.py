#!/usr/local/bin/python
# -*- coding: utf-8 -*-

__author__ = 'casimirdes'

"""
sobre:
    autor: matheusjm
    baseado no terminal serial do arduino, faremos algo parecido e utlizando
    a biblioteca tkinter para criacao do app
requisitos:
    pip install pyserial
"""

import tkinter as tk
import tkinter.ttk as ttk

import threading as th
import time
from sys import argv

import serial.tools.list_ports as ser_list_ports
import serial

print("INICIAL DO APP...")

lista_taxa = ("600", "1200", "2400", "4800", "9600", "19200", "38400", "57600", "76800",
              "115200", "128000", "230400", "460800", "576000", "921600", "1000000")

# mod para envio de pacote fixo para o outro dispositivo
FLAG_TIPO_TX = 1  # 0=nada no final, 1="\r\n" no final, 2=tamanho fixo de 'SIZE_MAX_UARTRX'
SIZE_MAX_UARTRX = 512
print("FLAG_TIPO_TX =", FLAG_TIPO_TX)
print("SIZE_MAX_UARTRX =", SIZE_MAX_UARTRX)

FLAG_TIPO_RX = 0  # 0=bruto somente o que vem, 1=add "\r\n" no final
FLAG_VALIDACAO_PACK = False

# manipula utf-8 rx
salve_byte = 0
flag_byte = False
# serial_port = None  # serial.Serial()
rx_thread = th.Thread()  # novo
# ======================================================================================================
# ======================================================================================================
# VARIAVEIS GLOBAIS
TAXA = 115200
PORTA = "COM6"
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

root = tk.Tk()
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
st_bytes_tx = tk.StringVar()
st_bytes_rx = tk.StringVar()

frame_bytes = tk.Frame(root, relief=tk.RIDGE, bg='#99dd99')  # , width=350, height=20)
frame_bytes.pack(side=tk.BOTTOM, anchor=tk.W, expand=tk.NO, fill=tk.BOTH)

tk.Label(frame_bytes, text="NÚMERO DE BYTES:", bg='#99dd99').pack(side=tk.LEFT, anchor=tk.W)

tk.Label(frame_bytes, textvariable=st_bytes_rx, bg='#99dd99').pack(side=tk.LEFT, anchor=tk.W, padx=5)
tk.Label(frame_bytes, textvariable=st_bytes_tx, bg='#99dd99').pack(side=tk.LEFT, anchor=tk.W, padx=5)

st_bytes_rx.set("RX (%u)" % BYTES_RX)
st_bytes_tx.set("TX (%u)" % BYTES_TX)
# -------------------------------------------------------------------------------------------


# LINHA DE REGISTRO DOS DADOS RECEBIDOS, TERMINAL...
# -------------------------------------------------------------------------------------------
frame_txt_terminal = tk.Frame(root, bg="green", relief=tk.RIDGE, width=100, height=20)
frame_txt_terminal.pack(side=tk.BOTTOM, anchor=tk.W, expand=tk.YES, fill=tk.BOTH)

textbox = tk.Text(frame_txt_terminal, font='{Consolas} 11')
textbox.pack(side=tk.LEFT, expand=tk.YES, fill=tk.BOTH)
textbox.insert(tk.INSERT, "Mensagens do terminal...\n")

scrollbar = tk.Scrollbar(frame_txt_terminal, orient=tk.VERTICAL)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

textbox.configure(yscrollcommand=scrollbar.set)

scrollbar.config(command=textbox.yview)

tk.Label(root, text="TERMINAL SERIAL", font='{Arial} 12', bg="#33aa66").pack(side=tk.BOTTOM, fill=tk.BOTH)
# -------------------------------------------------------------------------------------------


# LINHA DE ENVIO DE BYTES (CHAR, BYTE, STRING....)
# -------------------------------------------------------------------------------------------
frame_send = tk.Frame(root, bg="green", relief=tk.RIDGE, width=220, height=20)
frame_send.pack(side=tk.BOTTOM, anchor=tk.W, expand=tk.NO, fill=tk.BOTH)

send_entry = tk.Entry(frame_send, width=50, borderwidth=4)  # width=tamanho de caracteres...
send_entry.pack(side=tk.LEFT, anchor=tk.W, expand=tk.YES, fill=tk.X)
send_entry.insert(tk.END, "")

bt_send = tk.Button(frame_send, text=" ENVIAR ", bg='#22dd99', font='blod')
bt_send.pack(side=tk.LEFT, anchor=tk.W)
# -------------------------------------------------------------------------------------------


# LINHA DE STATUS E CONEXAO COM A PORTA SERIAL
# -------------------------------------------------------------------------------------------
frame_status = tk.Frame(root, bg="#99dd44", relief=tk.RIDGE, width=220, height=30)
frame_status.pack(side=tk.BOTTOM, anchor=tk.W, expand=tk.NO, fill=tk.BOTH)

bt_connect = tk.Button(frame_status, text="CONECTAR", font='blod')
bt_connect.pack(side=tk.LEFT, anchor=tk.W, padx=1, pady=1)
bt_connect.configure(bg="red")

st_status = tk.StringVar()
tk.Label(frame_status, textvariable=st_status, bg='#99dd44', font=11).pack(side=tk.LEFT, anchor=tk.W, padx=5)

bt_limpa = tk.Button(frame_status, text="LIMPA", font='blod')
bt_limpa.pack(side=tk.RIGHT, anchor=tk.W, padx=1, pady=1)

st_status.set(sms1)
# -------------------------------------------------------------------------------------------


# LINHA DE CONFIGURACAO DA PORTA DE SERIAL
# -------------------------------------------------------------------------------------------
frame_config = tk.Frame(root, bg="#9999dd", relief=tk.RIDGE, width=220, height=30)
frame_config.pack(side=tk.BOTTOM, anchor=tk.W, expand=tk.NO, fill=tk.BOTH)

# dados da porta:
tk.Label(frame_config, text="PORTA COM: ", bg="#9999dd", font=10).pack(side=tk.LEFT, anchor=tk.W)

port_entry = tk.Entry(frame_config, width=4, font=10)  # width=tamanho de caracteres...
port_entry.pack(side=tk.LEFT, anchor=tk.E)
port_entry.insert(tk.END, "6")

# dados de volocidade de conexao, baud rate(taxa) bps
tk.Label(frame_config, text="BAUD RATE: ", bg="#9999dd", font=10).pack(side=tk.LEFT)

combo_taxa = ttk.Combobox(frame_config, values=lista_taxa, state='readonly', width=6, font=10)
combo_taxa.pack(side=tk.LEFT)
combo_taxa.set(value=lista_taxa[9])

auto_down = tk.IntVar()
tk.Checkbutton(frame_config, text="Auto-rolagem", width=15, variable=auto_down, onvalue=1,
            offvalue=0, bg="#9999dd", font=10).pack(side=tk.RIGHT)


# -------------------------------------------------------------------------------------------


# ======================================================================================================
# ======================================================================================================
# FUNCOES DO APP


def checksum_xor_u8(buf, size):
    """
    retorna 'soma' xor de um buffer de bytes
    """
    checksum = 0
    for i in range(size):
        checksum ^= buf[i]
    return checksum


# uma vez definido uma variavel ou objeto ou entao tudo é objeto logo entao uma vez definido com global
# em uma so funcao para as demais funcoes essa variavel ja sera dita como global....


def chama_serial():
    global TAXA, PORTA, UART_OK
    # global rx_thread  # novo
    global serial_port

    if UART_OK:
        # verifica  porta serial e/ou se os outros timer foram ativados para desativar......
        UART_OK = False
        time.sleep(2)
        """
        if rx_thread.is_alive():
            rx_thread.do_run = False
            rx_thread.join()
        """
        # serial_port.close()
        print("PORTA SERIAL FECHADA")
        print("NUMERO TOTAL DE BYTES RECEBIDOS = %d" % BYTES_RX)
        print("NUMERO TOTAL DE BYTES TRANSMITIDOS = %d" % BYTES_TX)

        bt_connect.configure(bg="red")
        st_status.set(sms1)
    else:
        PORTA = "COM" + port_entry.get()
        TAXA = int(combo_taxa.get())

        conexao = "Porta = %s, Taxa = %s\n" % (PORTA, TAXA)  # cria string para imprimir no terminal...
        print(conexao)
        try:
            serial_port = serial.Serial(PORTA, TAXA)
            # serial_port.port = PORTA
            # serial_port.baudrate = TAXA
            serial_port.reset_input_buffer()  # flush input buffer, discarding all its contents
            serial_port.reset_output_buffer()  # flush output buffer, aborting current output

            UART_OK = True  # flag passa para verdadeiro

            textbox.insert(tk.END, "\nCONEXAO DA PORTA SERIAL ESTABELECIDA\n")
            textbox.insert(tk.END, conexao)
            textbox.yview(tk.END)

            bt_connect.configure(bg="green")
            # bt_connect.configure(state=DISABLED)

            st_status.set(sms2)

            # "segredo" esta aqui, funcao RX_DATA fica sendo atualizada a cada x ms, podem ser exploradas outras formas
            # como funçoes multithreads....
            # quanto mais rapida a taxa do serial menor deve ser o tempo de atualizacao (os ms)
            # para 50ms funciona ok para velocidades até 115200bps...
            ####root.after(50, RX_DATA)  # ja ativa a funcao de recepcao dos bytes via um "timer" em x tempo

            print("iniciando a thread")
            rx_thread = th.Thread(target=RX_DATA_th)  # chama a funcao real_time_adc para thread
            # ws_thread = th.Thread(target=websocket_thread, args=("websocket thread",))  # chama a funcao real_time_adc para thread
            rx_thread.start()

        except Exception as err:
            print(f"erro chama_serial er:{err}")
            textbox.insert(tk.END, "\nERRO DE CONEXÃO DE PORTA SERIAL \n")
            port_entry.delete(0, tk.END)
            port_entry.insert(tk.END, "1")
            textbox.yview(tk.END)
            UART_OK = False


def RX_DATA_th():
    global BYTES_RX
    message = bytearray()
    cont_erros = 0
    while UART_OK:
        try:
            if serial_port.is_open:
                while UART_OK:
                    cont_bytes = 0
                    message.clear()

                    while not serial_port.in_waiting and UART_OK is True:
                        time.sleep(0.01)  # 0.05 isso implica na velocidade da serial...
                        # print("x")

                    while True:
                        bytes_in = serial_port.in_waiting
                        if bytes_in>0:
                            result = serial_port.read(bytes_in)

                            if not result:
                                # cai fora pq nao tem mais nadaaa
                                break

                            cont_bytes += bytes_in
                            message += result
                            """
                            if result:
                                textbox.insert(END, result)
                                #print("cont", cont)
                            else:
                                break
                            """

                            time.sleep(0.001)  # 0.01
                        else:
                            break

                    # print("len message", len(message))
                    # textbox.insert(END, message.decode(encoding="utf-8"))

                    if cont_bytes > 0:
                        if FLAG_VALIDACAO_PACK:
                            # --------------------------------------------------------------------------------------
                            size = message[0] << 8 | message[1]
                            checksum1 = message[2]
                            if size < 513:
                                if cont_bytes == size + 3:
                                    checksum2 = checksum_xor_u8(message[3::], size)
                                else:
                                    cont_erros += 1
                                    checksum2 = 0
                            else:
                                cont_erros += 1
                                checksum2 = 0
                            sms = f"len message:{cont_bytes}/{len(message)}, size:{size}, checksum:{checksum1}=={checksum2}, cont_erros:{cont_erros}"
                            textbox.insert(tk.END, sms)
                            # --------------------------------------------------------------------------------------
                        else:
                            try:
                                sms_deco = message.decode(encoding="utf-8")
                            except Exception as err:
                                sms_deco = f"erro:{err}, sms:{message}"
                            textbox.insert(tk.END, sms_deco)

                        if FLAG_TIPO_RX == 1:
                            textbox.insert(tk.END, "\r\n")

                        if auto_down.get():  # retona um int...
                            textbox.yview(tk.END)  # configura o auto-relagem!!!!!

                        BYTES_RX += cont_bytes  # teste de contagem numero de bytes
                        # time.sleep(0.001)

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
        except Exception as err:
            cont_erros += 1
            print(f"erro except... nao tratado:, err:{err}, len:{len(message)}, cont_erros:{cont_erros}, serial_open:{serial_port.is_open}")
            """
            pc sonequinhaaa e acho que desativa a serial... e ai entra loop maluco
            erro except... nao tratado: ClearCommError failed (PermissionError(13, 'Acesso negado.', None, 5)) 0 838558
            erro except... nao tratado: ClearCommError failed (PermissionError(13, 'Acesso negado.', None, 5)) 0 838559
            erro except... nao tratado: ClearCommError failed (PermissionError(13, 'Acesso negado.', None, 5)) 0 838560
            erro except... nao tratado: ClearCommError failed (PermissionError(13, 'Acesso negado.', None, 5)) 0 838561
            """
    if not UART_OK:
        serial_port.close()
        print("fecha porta serial")
    print("saio do thread RX_DATA_th")


def envia_serial():
    global BYTES_TX
    data = send_entry.get()
    if len(data) > 0:
        if UART_OK:
            if serial_port.is_open:
                dataB = data.encode('utf-8')
                len_dataB = len(dataB)

                if FLAG_TIPO_TX == 2:  # fixo
                    pack = bytearray(SIZE_MAX_UARTRX)
                    pack[0:len_dataB] = dataB
                elif FLAG_TIPO_TX == 1:  # "\r\n"
                    pack = dataB + b"\r\n"
                else:  # nada no final
                    pack = dataB

                sss = "\n==============================================================\n"
                sss += ("PC ENVIA: %s\n" % data)
                sss += "==============================================================\n"
                textbox.insert(tk.END, sss)

                if auto_down.get():
                    textbox.yview(tk.END)

                BYTES_TX += len(pack)
                st_bytes_tx.set("TX (%u)" % BYTES_TX)

                time.sleep(0.01)
                # serial_port.write(pack)

                # ---------------------------------------------------------------------------
                header = bytearray(3)
                len_pack = len(pack)
                header[0] = (len_pack >> 8) & 0xff
                header[1] = len_pack & 0xff
                header[2] = checksum_xor_u8(pack, len_pack)
                pack_test = header + pack
                serial_port.write(pack_test)
                # ---------------------------------------------------------------------------
        send_entry.delete(0, tk.END)
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


def limpa_text_terminal():
    textbox.delete("1.0", tk.END)


# ======================================================================================================
# ======================================================================================================


# ======================================================================================================
# ======================================================================================================
# CONFIGURACOES DOS OBJETOS POS CRIACAO DAS FUNCOES

bt_connect.configure(command=chama_serial)
bt_limpa.configure(command=limpa_text_terminal)
bt_send.configure(command=envia_serial)

send_entry.bind("<KeyRelease>", envia_enter)
# ======================================================================================================
# ======================================================================================================


# ======================================================================================================
# verifica a existencia ou nao de portas COM no computador....
# isso nao funciona no LINUX... acho eu...
ports = list(ser_list_ports.comports())  # ports = list(serial.tools.list_ports.comports())
for p in ports:
    try:
        sms = "PORTA: " + str(p) + "\n"
        print(sms)
        textbox.insert(tk.END, sms)
    except Exception as err:
        print(f"Erro list_ports er:{err}")
        textbox.insert(tk.END, "NÃO FORAM ENCONTRADAS PORTAS <COM>\n PARA COMUNICAÇÃO\n")

if len(ports) == 0:
    textbox.insert(tk.END, "NÃO FORAM ENCONTRADAS PORTAS <COM> PARA COMUNICAÇÃO\n")
# ======================================================================================================


print("INICIAL LOOP DO TKINTER")

root.mainloop()

# verifica  porta serial e/ou se os outros timer foram ativados para desativar......
if UART_OK:
    UART_OK = False
    time.sleep(2)
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
