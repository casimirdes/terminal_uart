#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

"""
 ============================================================================
 Name			: terminal_uart
 Author			: matheus j. mella
 Version		: 0.2
 Date			: 29/10/25
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
from datetime import datetime

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

caminho_log_terminal = ""

perfil_carregado_nome = None  # Nome do perfil atualmente carregado
perfil_carregado = {}

lista_taxa = ("600", "1200", "2400", "4800", "9600", "19200", "38400",
              "57600", "76800", "115200", "128000", "230400", "460800",
              "576000", "921600", "1000000")

tipos_terminacao = "nada", "CR+LF (\\r\\n)", "CR (\\r)", "LF (\\n)"  # CR="\r" LF="\n"
bytes_terminacao = b"", b"\r\n", b"\r", b"\n"

# FLAG_TIPO_TX, FLAG_TIPO_TX = inteiro do index de 'tipos_terminacao'
FLAG_TIPO_TX = 3
FLAG_TIPO_RX = 3
FLAG_PACK_FIXO = False
SIZE_MAX_UARTRX = 0
FLAG_VALIDACAO_PACK = False


rx_thread = th.Thread()  # novo

TAXA = 115200
PORTA = "COM3"
UART_OK = False  # flag que indica se a conexao foi realizada ou nao

"""
from engineering_notation import EngNumber
for i in lista_taxa:
    tbit = 1/int(i)
    tbyte = (2+8)*tbit
    print(f"i:{i}bps, tbit:{EngNumber(tbit)}s, tbyte:{EngNumber(tbyte)}s")

    
i:600bps, tbit:1.67ms, tbyte:16.67ms
i:1200bps, tbit:833.33us, tbyte:8.33ms
i:2400bps, tbit:416.67us, tbyte:4.17ms
i:4800bps, tbit:208.33us, tbyte:2.08ms
i:9600bps, tbit:104.17us, tbyte:1.04ms
i:19200bps, tbit:52.08us, tbyte:520.83us
i:38400bps, tbit:26.04us, tbyte:260.42us
i:57600bps, tbit:17.36us, tbyte:173.61us
i:76800bps, tbit:13.02us, tbyte:130.21us
i:115200bps, tbit:8.68us, tbyte:86.81us
i:128000bps, tbit:7.81us, tbyte:78.12us
i:230400bps, tbit:4.34us, tbyte:43.40us
i:460800bps, tbit:2.17us, tbyte:21.70us
i:576000bps, tbit:1.74us, tbyte:17.36us
i:921600bps, tbit:1.09us, tbyte:10.85us
i:1000000bps, tbit:1us, tbyte:10us
"""

# =====================================================================================================================


# Abrir janela para criar ou editar
def janela_edicao_perfil(nome_perfil=None, dados_existentes=None):
    janela_edicao = tk.Toplevel(root)
    janela_edicao.title("Editar Perfil" if nome_perfil else "Novo Perfil")
    janela_edicao.geometry("300x350")
    janela_edicao.resizable(False, False)

    # nomes_param = ["PORTA:", "BAUD RATE:", "AUTO ROLAGEM:", "AUTO LOG:", "Terminação RX:", "Terminação TX:"]
    # porta:str,
    # baudrate:int,
    # auto_scrool:bool, # auto_log:bool,
    # txrx fixo:bool, se fixo n_bytes:int
    # rx: add final/terminação "\r\n", "\r", "\n", nada
    # tx: add final/terminação "\r\n", "\r", "\n", nada

    frame_edicao = tk.LabelFrame(janela_edicao, text="Configurações do Perfil", padx=10, pady=10)
    frame_edicao.pack(padx=10, pady=10, fill="x")

    padx_padrao = 8
    pady_padrao = 4

    frame_edicao.grid_columnconfigure(1, weight=1)

    tk.Label(frame_edicao, text="Nome do Perfil:").grid(row=0, column=0, padx=padx_padrao, pady=pady_padrao, sticky="w")
    entry_nome = tk.Entry(frame_edicao)
    entry_nome.grid(row=0, column=1, padx=padx_padrao, pady=pady_padrao, sticky="ew")

    tk.Label(frame_edicao, text="PORTA:").grid(row=1, column=0, padx=padx_padrao, pady=pady_padrao, sticky="w")
    entry_port = tk.Entry(frame_edicao)
    entry_port.grid(row=1, column=1, padx=padx_padrao, pady=pady_padrao, sticky="ew")

    tk.Label(frame_edicao, text="BAUD RATE: (bps)").grid(row=2, column=0, padx=padx_padrao, pady=pady_padrao, sticky="w")
    combo_taxa = ttk.Combobox(frame_edicao, values=lista_taxa, state='readonly', width=10)
    combo_taxa.grid(row=2, column=1, padx=padx_padrao, pady=pady_padrao, sticky="w")
    combo_taxa.set(lista_taxa[6])

    auto_down = tk.IntVar()
    tk.Checkbutton(frame_edicao, text="Auto-rolagem", variable=auto_down).grid(row=3, column=0, padx=padx_padrao, pady=pady_padrao, sticky="w")

    tk.Label(frame_edicao, text="Terminação RX").grid(row=4, column=0, padx=padx_padrao, pady=pady_padrao, sticky="w")
    combo_termrx = ttk.Combobox(frame_edicao, values=tipos_terminacao, state='readonly', width=12)
    combo_termrx.grid(row=4, column=1, padx=padx_padrao, pady=pady_padrao, sticky="w")
    combo_termrx.set(tipos_terminacao[0])

    tk.Label(frame_edicao, text="Terminação TX").grid(row=5, column=0, padx=padx_padrao, pady=pady_padrao, sticky="w")
    combo_termtx = ttk.Combobox(frame_edicao, values=tipos_terminacao, state='readonly', width=12)
    combo_termtx.grid(row=5, column=1, padx=padx_padrao, pady=pady_padrao, sticky="w")
    combo_termtx.set(tipos_terminacao[0])

    auto_log = tk.IntVar()
    tk.Checkbutton(frame_edicao, text="Auto-log", variable=auto_log).grid(row=6, column=0, padx=padx_padrao, pady=pady_padrao, sticky="w")

    def alternar_entry():
        if flag_pack_fixo.get() == 1:
            entry_pack_fixo.config(state="normal")
        else:
            entry_pack_fixo.config(state="disabled")

    flag_pack_fixo = tk.IntVar()
    frame_pack = tk.Frame(frame_edicao)
    frame_pack.grid(row=7, column=0, columnspan=2, sticky="w", padx=padx_padrao, pady=pady_padrao)
    tk.Checkbutton(frame_pack, text="Pack FIXO", variable=flag_pack_fixo, command=alternar_entry).pack(side="left")
    entry_pack_fixo = tk.Entry(frame_pack, width=5)
    entry_pack_fixo.pack(side="left", padx=(20, 5))
    tk.Label(frame_pack, text="(bytes)").pack(side="left")

    flag_pack_fixo.set(0)
    entry_pack_fixo.insert(0, "0")
    entry_pack_fixo.config(state="disabled")


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
        flag_pack_fixo.set(dados_existentes.get("flag_pack_fixo", 0))
        alternar_entry()
        entry_pack_fixo.delete(0, tk.END)
        entry_pack_fixo.insert(0, str(dados_existentes.get("pack_bytes", 0)))

    #parametros = entry_nome, entry_port, combo_taxa, auto_down, combo_termrx, combo_termtx, auto_log, flag_pack_fixo, entry_pack_fixo

    def salva_parametros():
        nome_perfil2 = entry_nome.get().strip()
        if not nome_perfil2:
            messagebox.showerror("Erro", "Nome do perfil é obrigatório.")
            return

        caminho_novo = os.path.join(PASTA_PERFIS, f"{nome_perfil2}.json")

        if os.path.exists(caminho_novo) and nome_perfil2 != nome_perfil:
            messagebox.showerror("Erro", "Já existe um perfil com esse nome.")
            return

        if nome_perfil and nome_perfil2 != nome_perfil:
            caminho_antigo = os.path.join(PASTA_PERFIS, f"{nome_perfil}.json")
            os.remove(caminho_antigo)

        dados = {
            "port": entry_port.get(),
            "taxa": int(combo_taxa.get()),
            "auto_down": auto_down.get(),
            "termrx": [combo_termrx.current(), combo_termrx.get()],
            "termtx": [combo_termtx.current(), combo_termtx.get()],
            "auto_log": auto_log.get(),
            "flag_pack_fixo": flag_pack_fixo.get(),
            "pack_bytes": int(entry_pack_fixo.get()),
        }
        print(f"DADOS JSON para salvar:{dados}")

        with open(caminho_novo, "w") as f:
            json.dump(dados, f)  # , indent=4

        messagebox.showinfo("Salvo", f"Perfil '{nome_perfil}' salvo com sucesso.")
        janela_edicao.destroy()
        atualizar_menu_perfis()

    #btn_salvar = tk.Button(janela_edicao, text="Salvar", command=lambda: salvar_parametros(parametros, janela_edicao, nome_perfil))
    btn_salvar = tk.Button(janela_edicao, text="Salvar", command=salva_parametros)
    btn_salvar.pack(pady=10)


# Criar novo perfil
def criar_novo_perfil():
    janela_edicao_perfil()


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
        texto = f"PORTA:{dados['port']} TAXA:{dados['taxa']}bps TERM RX:{dados['termrx'][1]} TX:{dados['termtx'][1]} Auto Rolagem:{dados['auto_down']} Auto Log:{dados['auto_log']}"
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
        janela_edicao_perfil(nome_perfil, dados)
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
    print("atualizar menu perfils")
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
def janela_sobre():
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
    link.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/casimirdes/terminal_uart"))


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
menu_ajuda.add_command(label="Sobre", command=janela_sobre)
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
    global TAXA, PORTA, UART_OK, FLAG_TIPO_RX, FLAG_TIPO_TX, FLAG_PACK_FIXO, SIZE_MAX_UARTRX
    # global rx_thread  # novo
    global serial_port
    global caminho_log_terminal

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

        FLAG_TIPO_RX = perfil_carregado["termrx"][0]
        FLAG_TIPO_TX = perfil_carregado["termtx"][0]
        if perfil_carregado["flag_pack_fixo"] == 0:
            FLAG_PACK_FIXO = False
        else:
            FLAG_PACK_FIXO = True
            SIZE_MAX_UARTRX = perfil_carregado["pack_bytes"]

        # DADOS JSON:{"port": "COM7", "taxa": 38400, "auto_down": 1, "termrx": [0, "CR+LF"], "termtx": [0, "CR+LF"], "auto_log": 1, "flag_pack_fixo": 0, "pack_bytes": 0}
        PORTA = perfil_carregado.get("port")
        TAXA = int(perfil_carregado.get("taxa"))

        # esquema do log em arquivo...
        time_log = time.strftime("%d%m%y_%H%M%S")  # perfil_DDMMAA_HHMMSS.log
        caminho_log_terminal = os.path.join(PASTA_LOGS, f"{perfil_carregado_nome}_{time_log}.txt")

        conexao = "Porta = %s, Taxa = %s\n" % (PORTA, TAXA)  # cria string para imprimir no terminal...
        print(conexao)
        try:
            serial_port = serial.Serial(PORTA, TAXA)
            # serial_port.port = PORTA
            # serial_port.baudrate = TAXA
            serial_port.reset_input_buffer()  # flush input buffer, discarding all its contents
            serial_port.reset_output_buffer()  # flush output buffer, aborting current output

            UART_OK = True  # flag passa para verdadeiro

            manda_text_terminal("\nCONEXAO DA PORTA SERIAL ESTABELECIDA\n")
            manda_text_terminal(conexao)
            """
            terminal_text.insert(tk.END, "\nCONEXAO DA PORTA SERIAL ESTABELECIDA\n")
            terminal_text.insert(tk.END, conexao)
            terminal_text.yview(tk.END)
            """

            bt_connect.configure(bg="green")
            # bt_connect.configure(state=DISABLED)

            st_status.set(sms2)

            print("iniciando a thread")
            rx_thread = th.Thread(target=fun_rx_data_th)  # chama a funcao real_time_adc para thread
            # ws_thread = th.Thread(target=websocket_thread, args=("websocket thread",))  # chama a funcao real_time_adc para thread
            rx_thread.start()

        except Exception as err:
            sms_erro = f"erro chama_serial er:{err}"
            manda_text_terminal(sms_erro)
            print(sms_erro)
            """
            terminal_text.insert(tk.END, "\nERRO DE CONEXÃO DE PORTA SERIAL \n")
            #port_entry.delete(0, tk.END)
            #port_entry.insert(tk.END, "1")
            terminal_text.yview(tk.END)
            """
            UART_OK = False


def registrar_logs_terminal(sms: str):
    if UART_OK:
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        linha_log = f"[{timestamp}] {sms}\n"
        """

        """
        if FLAG_TIPO_RX > 0:
            linha_log = sms.rstrip('\r\n') + '\n'
            linha_log += str_terminacao[FLAG_TIPO_RX]
        else:
            linha_log = sms
        """

        with open(caminho_log_terminal, 'a', encoding='utf-8') as arquivo_log:
            arquivo_log.write(sms)
        # arquivo ja é fechado automaticamente!!!!



def fun_rx_data_th():
    global BYTES_RX

    terminacaox = None
    if FLAG_TIPO_RX > 0:
        terminacaox = bytes_terminacao[FLAG_TIPO_RX]

    def ler_pacote_uart_line():
        # https://pyserial.readthedocs.io/en/latest/pyserial_api.html
        #result = serial_port.read_until(b"\r\n")
        result = serial_port.read_until(terminacaox)
        return result

    def ler_pacote_uart_loco():
        pacote = bytearray()
        while True:
            bytes_in = serial_port.in_waiting
            if bytes_in > 0:
                result = serial_port.read(bytes_in)
                pacote += result
                time.sleep(0.001)  # 0.01
            else:
                break
        return pacote

    def ler_pacote_uart_cru(tempo_silencio=0.05):
        pacote = bytearray()
        tempo_inicio = time.perf_counter()
        while True:
            if serial_port.in_waiting:
                dados = serial_port.read(serial_port.in_waiting)
                pacote += dados
                tempo_inicio = time.perf_counter()
            else:
                if time.perf_counter() - tempo_inicio > tempo_silencio:
                    break  # silêncio detectado → fim de pacote
                time.sleep(0.001)  # evita busy-wait
        return pacote

    while UART_OK:
        if serial_port.is_open:
            if terminacaox is None:
                #pacote = ler_pacote_uart_loco()
                pacote = ler_pacote_uart_cru()
            else:
                pacote = ler_pacote_uart_line()

            if pacote:
                print("bruto:", pacote)

                try:
                    sms_deco = pacote.decode("utf-8", errors="replace")
                except Exception as err:
                    sms_deco = f"erro:{err}, sms:{pacote}"

                manda_text_terminal(sms_deco)
                BYTES_RX += len(pacote)
        update_status_bytes()


def fun_rx_data_th_old():
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
                            #terminal_text.insert(tk.END, sms)
                            manda_text_terminal(sms)
                            # --------------------------------------------------------------------------------------
                        else:

                            print("bruto:", message)
                            try:
                                sms_deco = message.decode(encoding="utf-8")
                            except Exception as err:
                                sms_deco = f"erro:{err}, sms:{message}"
                            #terminal_text.insert(tk.END, sms_deco)
                            manda_text_terminal(sms_deco)

                        BYTES_RX += cont_bytes  # teste de contagem numero de bytes
                        # time.sleep(0.001)
                    update_status_bytes()  # st_bytes_rx.set("RX (%u)" % BYTES_RX)
                # serial_port.flushInput() #flush input buffer, discarding all its contents
                # serial_port.flushOutput()#flush output buffer, aborting current output

            update_status_bytes()  #st_bytes_rx.set("RX (%u)" % BYTES_RX)
        except Exception as err:
            cont_erros += 1
            sms_erro = f"erro except... nao tratado:, err:{err}, UART_OK:{UART_OK}, len:{len(message)}, cont_erros:{cont_erros}, serial_open:{serial_port.is_open}"
            manda_text_terminal(sms_erro)
            """
            pc sonequinhaaa e acho que desativa a serial... e ai entra loop maluco
            erro except... nao tratado: ClearCommError failed (PermissionError(13, 'Acesso negado.', None, 5)) 0 838558
            erro except... nao tratado: ClearCommError failed (PermissionError(13, 'Acesso negado.', None, 5)) 0 838559
            erro except... nao tratado: ClearCommError failed (PermissionError(13, 'Acesso negado.', None, 5)) 0 838560
            erro except... nao tratado: ClearCommError failed (PermissionError(13, 'Acesso negado.', None, 5)) 0 838561
            """
    if not UART_OK:
        serial_port.close()
        sms_byby = "fecha porta serial"
        manda_text_terminal(sms_byby)
    print("saio do thread RX_DATA_th")


def envia_serial():
    global BYTES_TX
    sms_tx = send_entry.get()
    if len(sms_tx) > 0:
        if UART_OK:
            if serial_port.is_open:
                dataB = sms_tx.encode('utf-8')

                if FLAG_PACK_FIXO:
                    len_dataB = len(dataB)
                    pack = bytearray(SIZE_MAX_UARTRX)
                    pack[0:len_dataB] = dataB
                elif FLAG_TIPO_TX > 0:
                    pack = dataB + bytes_terminacao[FLAG_TIPO_TX]
                else:  # nada no final
                    pack = dataB

                sss = "\n==============================================================\n"
                sss += ("PC ENVIA: %s\n" % sms_tx)
                sss += "==============================================================\n"
                manda_text_terminal(sss)

                BYTES_TX += len(pack)
                update_status_bytes()  #st_bytes_tx.set("TX (%u)" % BYTES_TX)

                time.sleep(0.01)

                if FLAG_VALIDACAO_PACK:
                    # ---------------------------------------------------------------------------
                    header = bytearray(3)
                    len_pack = len(pack)
                    header[0] = (len_pack >> 8) & 0xff
                    header[1] = len_pack & 0xff
                    header[2] = checksum_xor_u8(pack, len_pack)
                    pack_test = header + pack
                    serial_port.write(pack_test)
                    # ---------------------------------------------------------------------------
                else:
                    serial_port.write(pack)

        send_entry.delete(0, tk.END)


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


def manda_text_terminal(sms: str):

    sms_ajustado = sms.rstrip('\r\n') + '\n'

    terminal_text.insert(tk.END, sms_ajustado)

    if auto_down.get():  # retona um int...
        terminal_text.yview(tk.END)  # configura o auto-relagem!!!!!

    if auto_log.get():
        registrar_logs_terminal(sms_ajustado)

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
        sms = f"PORTA:{p}"
        print(sms)
        #terminal_text.insert(tk.END, sms)
        manda_text_terminal(sms)
    except Exception as err:
        sms_erro = f"Erro list_ports er:{err}"
        #terminal_text.insert(tk.END, "NÃO FORAM ENCONTRADAS PORTAS <COM>\n PARA COMUNICAÇÃO\n")
        manda_text_terminal(sms_erro)
        manda_text_terminal("NÃO FORAM ENCONTRADAS PORTAS PARA COMUNICAÇÃO")

if len(ports) == 0:
    #terminal_text.insert(tk.END, "NÃO FORAM ENCONTRADAS PORTAS <COM> PARA COMUNICAÇÃO\n")
    manda_text_terminal("NÃO FORAM ENCONTRADAS PORTAS <COM> PARA COMUNICAÇÃO")
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
