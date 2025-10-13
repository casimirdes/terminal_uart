#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

"""
 ============================================================================
 Name			: terminal_uart
 Author			: matheus j. mella
 Version		: 0.1
 Date			: 12/10/25
 Description 	: terminal serial uart
 GitHub			: https://github.com/casimirdes/terminal_uart
 ============================================================================


"""


import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import json
import os
import webbrowser
import subprocess
import platform

import threading as th
import time
import serial.tools.list_ports as ser_list_ports
import serial

#import psutil
import tracemalloc


# =====================================================================================================================
# variavies globais...

BYTES_RX, BYTES_TX = 0, 0
sms1 = "Dipositivo não conectado!"
sms2 = "Dispositivo conectado!"

PASTA_PERFIS = "perfis"
PASTA_LOGS = "logs"
os.makedirs(PASTA_PERFIS, exist_ok=True)
os.makedirs(PASTA_LOGS, exist_ok=True)

perfil_carregado_nome = None  # Nome do perfil atualmente carregado
perfil_carregado = {}

lista_taxa = ("600", "1200", "2400", "4800", "9600", "19200", "38400",
              "57600", "76800", "115200", "128000", "230400", "460800",
              "576000", "921600", "1000000")

terminacao = "CR+LF", "CR", "LF", "nada"  # CR="\r" LF="\n"

# mod para envio de pacote fixo para o outro dispositivo
FLAG_TIPO_TX = 1  # 0=nada no final, 1="\r\n" no final, 2=tamanho fixo de 'SIZE_MAX_UARTRX'
SIZE_MAX_UARTRX = 512
FLAG_TIPO_RX = 0  # 0=bruto somente o que vem, 1=add "\r\n" no final
FLAG_VALIDACAO_PACK = False

rx_thread = th.Thread()  # novo

TAXA = 115200
PORTA = "COM3"
UART_OK = False  # flag que indica se a conexao foi realizada ou nao

# =====================================================================================================================


# Salvar perfil
def salvar_parametros(parametros, janela_edicao, nome_antigo=None):
    entry_nome, entry_port, combo_taxa, auto_down, combo_termrx, combo_termtx, auto_log = parametros

    nome_perfil = entry_nome.get().strip()
    if not nome_perfil:
        messagebox.showerror("Erro", "Nome do perfil é obrigatório.")
        return

    caminho_novo = os.path.join(PASTA_PERFIS, f"{nome_perfil}.json")

    if os.path.exists(caminho_novo) and nome_perfil != nome_antigo:
        messagebox.showerror("Erro", "Já existe um perfil com esse nome.")
        return

    if nome_antigo and nome_perfil != nome_antigo:
        caminho_antigo = os.path.join(PASTA_PERFIS, f"{nome_antigo}.json")
        os.remove(caminho_antigo)

    dados = {
        "port": entry_port.get(),
        "taxa": int(combo_taxa.get()),
        "auto_down": auto_down.get(),
        "termrx": [combo_termrx.current(), combo_termrx.get()],
        "termtx": [combo_termtx.current(), combo_termtx.get()],
        "auto_log": auto_log.get(),
    }
    print(f"DADOS JSON:{dados}")

    with open(caminho_novo, "w") as f:
        json.dump(dados, f)  # , indent=4

    messagebox.showinfo("Salvo", f"Perfil '{nome_perfil}' salvo com sucesso.")
    janela_edicao.destroy()
    atualizar_menu_perfis()


# Abrir janela para criar ou editar
def abrir_janela_edicao(nome_perfil=None, dados_existentes=None):
    janela_edicao = tk.Toplevel(root)
    janela_edicao.title("Editar Perfil" if nome_perfil else "Novo Perfil")
    janela_edicao.geometry("300x300")

    # nomes_param = ["PORTA:", "BAUD RATE:", "AUTO ROLAGEM:", "AUTO LOG:", "Terminação RX:", "Terminação TX:"]
    # porta:str,
    # baudrate:int,
    # auto_scrool:bool, # auto_log:bool,
    # txrx fixo:bool, se fixo n_bytes:int
    # rx: add final/terminação "\r\n", "\r", "\n", nada
    # tx: add final/terminação "\r\n", "\r", "\n", nada

    frame_edicao = tk.Frame(janela_edicao)
    frame_edicao.pack(pady=10)

    tk.Label(frame_edicao, text="Nome do Perfil:").grid(row=0, column=0, padx=5)
    entry_nome = tk.Entry(frame_edicao)
    entry_nome.grid(row=0, column=1, padx=5)

    tk.Label(frame_edicao, text="PORTA:").grid(row=1, column=0, padx=5)
    entry_port = tk.Entry(frame_edicao)
    entry_port.grid(row=1, column=1, padx=5)

    tk.Label(frame_edicao, text="BAUD RATE: (bps)").grid(row=2, column=0, padx=5)
    combo_taxa = ttk.Combobox(frame_edicao, values=lista_taxa, state='readonly', width=10)  # , width=6, font=10
    combo_taxa.grid(row=2, column=1, padx=5)
    combo_taxa.set(value=lista_taxa[6])

    auto_down = tk.IntVar()
    tk.Checkbutton(frame_edicao, text="Auto-rolagem", width=15, variable=auto_down, onvalue=1,
                offvalue=0).grid(row=3, column=0, padx=5)  # , font=10, , bg="#9999dd"
    # dados["auto_rolagem"] = auto_down.get()

    tk.Label(frame_edicao, text="Terminação RX").grid(row=4, column=0, padx=5)
    combo_termrx = ttk.Combobox(frame_edicao, values=terminacao, state='readonly', width=8)  # , width=6, font=10
    combo_termrx.grid(row=4, column=1, padx=5)
    combo_termrx.set(value=terminacao[0])

    tk.Label(frame_edicao, text="Terminação TX").grid(row=5, column=0, padx=5)
    combo_termtx = ttk.Combobox(frame_edicao, values=terminacao, state='readonly', width=8)  # , width=6, font=10
    combo_termtx.grid(row=5, column=1, padx=5)
    combo_termtx.set(value=terminacao[0])

    auto_log = tk.IntVar()
    tk.Checkbutton(frame_edicao, text="Auto-log", width=15, variable=auto_log, onvalue=1,
                offvalue=0).grid(row=6, column=0, padx=5)  # , font=10, , bg="#9999dd"

    if nome_perfil:
        entry_nome.insert(0, nome_perfil)

    if dados_existentes:
        print(f"dados_existentes:{dados_existentes}")
        # {'port': '13', 'taxa': 1000000, 'auto_down': 1, 'termrx': [1, 'CR'], 'termtx': [0, 'CR+LF']}
        entry_port.insert(0, dados_existentes.get("port", ""))
        combo_taxa.set(value=dados_existentes.get("taxa", ""))
        auto_down.set(dados_existentes.get("auto_down", 0))
        combo_termrx.current(dados_existentes.get("termrx", 0)[0])
        combo_termtx.current(dados_existentes.get("termtx", 0)[0])
        auto_log.set(dados_existentes.get("auto_log", 0))

    parametros = entry_nome, entry_port, combo_taxa, auto_down, combo_termrx, combo_termtx, auto_log

    btn_salvar = tk.Button(janela_edicao, text="Salvar", command=lambda: salvar_parametros(parametros, janela_edicao, nome_perfil))
    btn_salvar.pack(pady=10)


# Criar novo perfil
def criar_novo_perfil():
    abrir_janela_edicao()


# Carregar perfil
def carregar_perfil(nome_perfil):
    global perfil_carregado_nome, perfil_carregado
    if UART_OK:
        print("porta serial ativa, desconecte pra carregar novo perfil!!!")
        messagebox.showwarning(
            "Aviso",
            "Porta serial ativada, desconecte para carregar um novo perfil"
        )

        return
    caminho = os.path.join(PASTA_PERFIS, f"{nome_perfil}.json")
    try:
        with open(caminho, "r") as f:
            dados = json.load(f)

        root.title(nome_perfil)  # atualiza para nome do perfil
        # {"port": "3", "taxa": 1000000, "auto_down": 1, "termrx": [0, "CR+LF"], "termtx": [2, "LF"], "auto_log": 1}
        texto = f"PORTA:{dados["port"]} TAXA:{dados["taxa"]}bps TERM RX:{dados["termrx"][1]} TX:{dados["termtx"][1]} Auto Rolagem:{dados["auto_down"]} Auto Log:{dados["auto_log"]}"
        #label_parametros.config(text=texto)
        label_perfil.config(text=texto)
        perfil_carregado_nome = nome_perfil
        perfil_carregado = dados

        auto_down.set(dados["auto_down"])
        auto_log.set(dados["auto_log"])

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao carregar perfil: {e}")


# Editar perfil
def editar_perfil(nome_perfil):
    caminho = os.path.join(PASTA_PERFIS, f"{nome_perfil}.json")
    try:
        with open(caminho, "r") as f:
            dados = json.load(f)
        abrir_janela_edicao(nome_perfil, dados)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao editar perfil: {e}")


# Excluir perfil
def excluir_perfil(nome_perfil):
    if nome_perfil == perfil_carregado_nome:
        messagebox.showwarning("Aviso", "Não é possível excluir o perfil atualmente carregado. Carregue outro antes.")
        return

    resposta = messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o perfil '{nome_perfil}'?")
    if resposta:
        caminho = os.path.join(PASTA_PERFIS, f"{nome_perfil}.json")
        try:
            os.remove(caminho)
            atualizar_menu_perfis()
            messagebox.showinfo("Excluído", f"Perfil '{nome_perfil}' foi excluído.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir perfil: {e}")


# Atualizar menu
def atualizar_menu_perfis():
    menu_config.delete(0, 'end')
    menu_config.add_command(label="Criar Novo Perfil", command=criar_novo_perfil)
    menu_config.add_separator()

    arquivos = sorted([f for f in os.listdir(PASTA_PERFIS) if f.endswith(".json")])
    if arquivos:
        for arquivo in arquivos:
            nome = arquivo[:-5]  # ignora ".json"
            submenu = tk.Menu(menu_config, tearoff=0)
            submenu.add_command(label="Carregar", command=lambda n=nome: carregar_perfil(n))
            submenu.add_command(label="Editar", command=lambda n=nome: editar_perfil(n))
            submenu.add_command(label="Excluir", command=lambda n=nome: excluir_perfil(n))
            menu_config.add_cascade(label=nome, menu=submenu)
    else:
        menu_config.add_command(label="(Nenhum perfil salvo)", state="disabled")

    menu_config.add_separator()
    menu_config.add_command(label="Sair", command=root.quit)


# Abrir pasta de logs
def abrir_pasta_logs():
    caminho_absoluto = os.path.abspath(PASTA_LOGS)
    if platform.system() == "Windows":
        os.startfile(caminho_absoluto)
    elif platform.system() == "Darwin":  # macOS
        subprocess.run(["open", caminho_absoluto])
    else:  # Linux
        subprocess.run(["xdg-open", caminho_absoluto])


# Abrir janela de "Sobre"
def abrir_janela_sobre():
    janela = tk.Toplevel(root)
    janela.title("Sobre")
    janela.geometry("290x110")
    janela.maxsize(290, 110)
    texto = """
    Terminal serial uart, para delírio dos que curtem
    Desenvolvido por casimirdes
    Acesse o site:
    """

    label = tk.Label(janela, text=texto, justify="left")
    label.pack()  # pady=5

    link = tk.Label(janela, text="github casimirdes", fg="blue", cursor="hand2")
    link.pack()
    link.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/casimirdes"))


# =======================================================================================================
# =======================================================================================================
root = tk.Tk()
root.geometry("600x400")
root.title("Terminal UART")

# Menu principal
menu_bar = tk.Menu(root)

# Menu de configurações
menu_config = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Configurações", menu=menu_config)

# Menu de logs
menu_logs = tk.Menu(menu_bar, tearoff=0)
menu_logs.add_command(label="Abrir pasta de logs", command=abrir_pasta_logs)
menu_bar.add_cascade(label="Logs", menu=menu_logs)

# Menu de ajuda
menu_ajuda = tk.Menu(menu_bar, tearoff=0)
menu_ajuda.add_command(label="Sobre", command=abrir_janela_sobre)
menu_bar.add_cascade(label="Ajuda", menu=menu_ajuda)

# Aplica menu na janela
root.config(menu=menu_bar)

# Frame principal usando grid
frame_principal = tk.Frame(root)
frame_principal.grid(row=0, column=0, sticky="nsew")

# Permitir expansão do frame_principal
root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)

# Configurar linhas do frame_principal
for i in range(5):
    frame_principal.rowconfigure(i, weight=0)  # linhas fixas para labels
frame_principal.rowconfigure(4, weight=1)  # linha do Text cresce
frame_principal.rowconfigure(5, weight=0)  # linha de status
frame_principal.columnconfigure(0, weight=1)

# ---------------------------------------------------------------------------------------------
# Label do perfil
label_perfil = tk.Label(frame_principal, text="Perfil carregado: Nenhum", anchor="w")
label_perfil.grid(row=0, column=0, sticky="ew", padx=10, pady=(5, 0))
# ---------------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------------
# LINHA DE STATUS E CONEXAO COM A PORTA SERIAL
frame_conexao = tk.Frame(frame_principal, bg="#99dd44")
frame_conexao.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
frame_conexao.rowconfigure(0, weight=1)
frame_conexao.columnconfigure(0, weight=1)
bt_connect = tk.Button(frame_conexao, text="CONECTAR")  # font='blod'
bt_connect.pack(side=tk.LEFT, anchor=tk.W, padx=1, pady=1)
bt_connect.configure(bg="red")
st_status = tk.StringVar()
tk.Label(frame_conexao, textvariable=st_status, bg='#99dd44').pack(side=tk.LEFT, anchor=tk.W, padx=5)  # font=11
st_status.set(sms1)
bt_limpa = tk.Button(frame_conexao, text="LIMPA", bg="#9999dd")
bt_limpa.pack(side=tk.RIGHT, anchor=tk.W, padx=1, pady=1)
auto_down = tk.IntVar()
tk.Checkbutton(frame_conexao, text="Auto-rolagem", variable=auto_down, onvalue=1, offvalue=0, bg="#9999dd").pack(side=tk.RIGHT)
auto_log = tk.IntVar()
tk.Checkbutton(frame_conexao, text="Auto-log", variable=auto_log, onvalue=1, offvalue=0, bg="#9999dd").pack(side=tk.RIGHT)
# ---------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------
# linha de envido
frame_send = tk.Frame(frame_principal)  # relief=tk.RIDGE, width=220, height=20
#frame_send.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
frame_send.grid(row=2, column=0, sticky="ew", padx=10, pady=(2, 0))
send_entry = tk.Entry(frame_send, width=50, borderwidth=4)  # width=tamanho de caracteres...
send_entry.pack(side=tk.LEFT, anchor=tk.W, expand=tk.YES, fill=tk.X)
send_entry.insert(tk.END, "")
bt_send = tk.Button(frame_send, text="ENVIAR", bg='#22dd99')
bt_send.pack(side=tk.LEFT, anchor=tk.W)
# ---------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------
# Label do terminal

frame_send = tk.Frame(frame_principal)  # relief=tk.RIDGE, width=220, height=20
frame_send.grid(row=3, column=0, sticky="ew", padx=10, pady=(2, 0))
label_terminal = tk.Label(frame_send, text="TERMINAL SERIAL", anchor="w")
label_terminal.grid(row=2, column=0, sticky="ew", padx=10, pady=(2, 0))

#label_terminal = tk.Label(frame_principal, text="TERMINAL SERIAL", anchor="w")
#label_terminal.grid(row=2, column=0, sticky="ew", padx=10, pady=(2, 0))
# ---------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------
# Frame para Text + Scrollbar
frame_texto = tk.Frame(frame_principal)
frame_texto.grid(row=4, column=0, sticky="nsew", padx=10, pady=5)
frame_texto.rowconfigure(0, weight=1)
frame_texto.columnconfigure(0, weight=1)

# Scrollbar
scrollbar = tk.Scrollbar(frame_texto)
scrollbar.grid(row=0, column=1, sticky="ns")
scrollbar_horizontal = tk.Scrollbar(frame_texto, orient="horizontal")
scrollbar_horizontal.grid(row=1, column=0, sticky="ew")

# Text widget
terminal_text = tk.Text(frame_texto, wrap="none", yscrollcommand=scrollbar.set, xscrollcommand=scrollbar_horizontal.set)  # , state="disabled"
terminal_text.grid(row=0, column=0, sticky="nsew")
scrollbar.config(command=terminal_text.yview)
scrollbar_horizontal.config(command=terminal_text.xview)

#- "word" → quebra a linha sem cortar palavras.
#- "char" → quebra a linha caractere por caractere, mesmo no meio de palavras.
#- "none" → não quebra a linha, e o texto vai além da borda (precisa de scrollbar horizontal).

def alternar_wrap():
    atual = terminal_text.cget("wrap")
    if atual == "none":
        terminal_text.config(wrap="word")
        scrollbar_horizontal.grid_remove()
    else:
        terminal_text.config(wrap="none")
        scrollbar_horizontal.grid()

# Exemplo no terminal
terminal_text.insert("end", "Mensagens do terminal...\n")
# ---------------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------------
# Linha de status TX/RX
status_var = tk.StringVar()
label_status = tk.Label(frame_principal, textvariable=status_var, anchor="w", relief="sunken", bg="#f0f0f0")
label_status.grid(row=5, column=0, sticky="ew", padx=10, pady=(0, 5))
status_var.set(f"NÚMERO DE BYTES:  TX:{BYTES_TX}  RX:{BYTES_RX}")
# ---------------------------------------------------------------------------------------------


def update_status_bytes():
    # como são globais...
    #tracemalloc.start()
    current, peak = tracemalloc.get_traced_memory()
    #print(f"Memória atual: {current / 1024:.2f} KB")
    #print(f"Pico de memória: {peak / 1024:.2f} KB")

    tamanho_texto = len(terminal_text.get("1.0", "end-1c"))
    #print(f"Tamanho atual do texto: {tamanho_texto} caracteres")

    status_var.set(f"NÚMERO DE BYTES:  TX:{BYTES_TX}  RX:{BYTES_RX}     RAM:{current / 1024:.2f}/{peak / 1024:.2f} KB     BUFF:{tamanho_texto}")

"""
# Exemplo de conteúdo
for i in range(50):
    terminal_text.insert("end", f"Linha {i + 1}\n")
terminal_text.yview(tk.END)  # configura o auto-relagem!!!!!
"""

# ======================================================================================================
# ======================================================================================================
# FUNCOES da parte terminal serial

def checksum_xor_u8(buf, size):
    """
    retorna 'soma' xor de um buffer de bytes
    """
    checksum = 0
    for i in range(size):
        checksum ^= buf[i]
    return checksum


def chama_serial():
    global TAXA, PORTA, UART_OK
    # global rx_thread  # novo
    global serial_port

    if UART_OK:
        # verifica  porta serial e/ou se os outros timer foram ativados para desativar......
        UART_OK = False
        time.sleep(1)
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

        tracemalloc.start()
        current, peak = tracemalloc.get_traced_memory()
        print(f"Memória atual: {current / 1024:.2f} KB")
        print(f"Pico de memória: {peak / 1024:.2f} KB")


        if not perfil_carregado:
            print("PERFIL NÃO CARREGADO")
            return

        print("perfil_carregado_nome:", perfil_carregado_nome)
        print("perfil_carregado:", perfil_carregado)

        """
        dados = {
        "port": entry_port.get(),
        "taxa": int(combo_taxa.get()),
        "auto_down": auto_down.get(),
        "termrx": [combo_termrx.current(), combo_termrx.get()],
        "termtx": [combo_termtx.current(), combo_termtx.get()],
        "auto_log": auto_log.get(),
        }"""
        # DADOS JSON:{'port': 'COM3', 'taxa': 115200, 'auto_down': 1, 'termrx': [0, 'CR+LF'], 'termtx': [0, 'CR+LF'], 'auto_log': 1}
        PORTA = perfil_carregado.get("port")
        TAXA = int(perfil_carregado.get("taxa"))

        conexao = "Porta = %s, Taxa = %s\n" % (PORTA, TAXA)  # cria string para imprimir no terminal...
        print(conexao)
        try:
            serial_port = serial.Serial(PORTA, TAXA)
            # serial_port.port = PORTA
            # serial_port.baudrate = TAXA
            serial_port.reset_input_buffer()  # flush input buffer, discarding all its contents
            serial_port.reset_output_buffer()  # flush output buffer, aborting current output

            UART_OK = True  # flag passa para verdadeiro

            terminal_text.insert(tk.END, "\nCONEXAO DA PORTA SERIAL ESTABELECIDA\n")
            terminal_text.insert(tk.END, conexao)
            terminal_text.yview(tk.END)

            bt_connect.configure(bg="green")
            # bt_connect.configure(state=DISABLED)

            st_status.set(sms2)

            # "segredo" esta aqui, funcao RX_DATA fica sendo atualizada a cada x ms, podem ser exploradas outras formas
            # como funçoes multithreads....
            # quanto mais rapida a taxa do serial menor deve ser o tempo de atualizacao (os ms)
            # para 50ms funciona ok para velocidades até 115200bps...
            ####root.after(50, RX_DATA)  # ja ativa a funcao de recepcao dos bytes via um "timer" em x tempo

            print("iniciando a thread")
            rx_thread = th.Thread(target=fun_rx_data_th)  # chama a funcao real_time_adc para thread
            # ws_thread = th.Thread(target=websocket_thread, args=("websocket thread",))  # chama a funcao real_time_adc para thread
            rx_thread.start()

        except Exception as err:
            print(f"erro chama_serial er:{err}")
            terminal_text.insert(tk.END, "\nERRO DE CONEXÃO DE PORTA SERIAL \n")
            #port_entry.delete(0, tk.END)
            #port_entry.insert(tk.END, "1")
            terminal_text.yview(tk.END)
            UART_OK = False


def fun_rx_data_th():
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
                            terminal_text.insert(tk.END, sms)
                            # --------------------------------------------------------------------------------------
                        else:
                            try:
                                sms_deco = message.decode(encoding="utf-8")
                            except Exception as err:
                                sms_deco = f"erro:{err}, sms:{message}"
                            terminal_text.insert(tk.END, sms_deco)

                        if FLAG_TIPO_RX == 1:
                            terminal_text.insert(tk.END, "\r\n")

                        if auto_down.get():  # retona um int...
                            terminal_text.yview(tk.END)  # configura o auto-relagem!!!!!

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
                    update_status_bytes()  # st_bytes_rx.set("RX (%u)" % BYTES_RX)
                # serial_port.flushInput() #flush input buffer, discarding all its contents
                # serial_port.flushOutput()#flush output buffer, aborting current output

            update_status_bytes()  #st_bytes_rx.set("RX (%u)" % BYTES_RX)
        except Exception as err:
            cont_erros += 1
            print(f"erro except... nao tratado:, err:{err}, UART_OK:{UART_OK}, len:{len(message)}, cont_erros:{cont_erros}, serial_open:{serial_port.is_open}")
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
                terminal_text.insert(tk.END, sss)

                if auto_down.get():
                    terminal_text.yview(tk.END)

                BYTES_TX += len(pack)
                update_status_bytes()  #st_bytes_tx.set("TX (%u)" % BYTES_TX)

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
    terminal_text.delete("1.0", tk.END)


# ======================================================================================================
# ======================================================================================================


# ======================================================================================================
# ======================================================================================================
# CONFIGURACOES DOS OBJETOS POS CRIACAO DAS FUNCOES

bt_connect.configure(command=chama_serial)
bt_limpa.configure(command=limpa_text_terminal)
bt_send.configure(command=envia_serial)

send_entry.bind("<KeyRelease>", envia_enter)

# Atualizar perfis no menu
atualizar_menu_perfis()
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
        terminal_text.insert(tk.END, sms)
    except Exception as err:
        print(f"Erro list_ports er:{err}")
        terminal_text.insert(tk.END, "NÃO FORAM ENCONTRADAS PORTAS <COM>\n PARA COMUNICAÇÃO\n")

if len(ports) == 0:
    terminal_text.insert(tk.END, "NÃO FORAM ENCONTRADAS PORTAS <COM> PARA COMUNICAÇÃO\n")
# ======================================================================================================

try:
    print("INICIAL LOOP DO TKINTER")
    root.mainloop()
except Exception as err:
    print(f"Erro mainloop: {err}")
finally:
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
