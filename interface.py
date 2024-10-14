from customtkinter import *
from tkinter import ttk
from PIL import Image
import backend, api, helper
import traceback
from CTkMessagebox import CTkMessagebox
import serial
import time

class TrueBuyInterface:
    def __init__(self, root, tela_width):
        self.root = root
        self.tela_width = tela_width
        #variaveis para controle de janelas toplevel
        self.yon = False
        self.tp_0 = self.tp_1 = self.tp_2 = self.tp_3 = self.tp_4 = self.tp_5 = self.tp_6 = self.tp_7 = self.tp_8 = self.tp_9 = self.tp_password = None
        #varivaveis para controle de labels content
        self.current_subtotal = helper.format_to_moeda(0) #subtotal atual
        self.lista_product_ids = []
        #estilização 
        style = ttk.Style()
        style.map("Treeview", 
                background=[("selected", "green")])
        style.configure("Treeview", font=("arial", 12))
        style.configure("Treeview.Heading", font=("Arial", 12, 'bold'))

        #outras definições
        self.formas_pgmt_ativas = ('dinheiro', 'débito', 'crédito', 'pix')
        self.fonte_basic = CTkFont('arial', 15, 'bold')
        self.tp_0_fonte_padrao_bold = CTkFont('arial', 20, 'bold')
        self.tp_0_fonte_padrao = CTkFont('arial', 20)
        self.general_product_id = '20'
        self.customer_id = 0
        self.sangria_categorias = ('Pagamento de Mercadoria', 'Pagamento de Vale', 'Outro')
        self.products_table_columns = ('id', 'barcode','descricao', 'ncm', 'ncm_desc', 'marca', 'nome', 'price', 'quantity', 'source', 'data_vencimento')
        self.version = '1.0'
        self.contato = '51 989705423'
        self.tp_password_feedback = False

        self.abrir_interface_root()

    def abrir_gaveta(self):
        # Ajuste a porta COM conforme necessário
        com_port = 'COM2'  # Substitua pela sua porta correta
        baud_rate = 9600

        # Comando para abrir a gaveta
        open_drawer_command = b'\x1B\x70\x00\x19\xFA'  # ESC p 0 25 250

        # Enviar comando
        try:
            with serial.Serial(com_port, baud_rate, timeout=1) as printer:
                printer.write(open_drawer_command)
                printer.flush()
                time.sleep(1)  # Aguarda um segundo
                print("Gaveta de caixa aberta.")
        except Exception as e:
            print(f"Erro ao abrir a gaveta: {e}")


    def get_yes_or_not(self, janela, ask='Confirmar esta operação?'):
        if self.yon == False:
            msg = CTkMessagebox(janela, title="Confirmar operação?", message=ask,
                            icon="question", option_2="Sim", option_1="Não", option_focus=2, font=self.fonte_basic)
            self.yon = True
            msg.grab_set()
            response = msg.get()
            if response == 'Sim':
                self.yon = False
                return True

            self.yon = False
            return False

    def abrir_tp_password(self, janela):

        self.tp_password = CTkToplevel(janela)
        self.tp_password.attributes('-topmost', 'true')
        self.tp_password.title('Inserir Senha')
        self.tp_password_width = 500
        self.tp_password_height = 250
        self.tp_password_x = self.root.winfo_width()//2 - self.tp_password_width//2   #essa e algumas abaixo, sao linhas que centralizam o tp na root
        self.tp_password_y = self.root.winfo_height()//2 - self.tp_password_height//2
        self.tp_password.geometry(f'{self.tp_password_width}x{self.tp_password_height}+{self.tp_password_x}+{self.tp_password_y}')
        self.tp_password.resizable(False, False)
        self.tp_password.grab_set()

        
        titlo = CTkLabel(self.tp_password, text='Inserir senha para prosseguir:', font=CTkFont('arial', 30, 'bold'))
        titlo.place(relx=0.5, rely=0.05, anchor='n')

        self.tp_password_entry = CTkEntry(self.tp_password, width=400, height=50, font=self.tp_0_fonte_padrao_bold)
        self.tp_password_entry.place(relx=0.5, rely=0.3, anchor='n')
        self.entry_sinalizer = CTkLabel(self.tp_password, text='Senha inválida', text_color='red')

        button_ok=CTkButton(self.tp_password, text='Confirmar', font=self.tp_0_fonte_padrao_bold, height = 50, command=lambda:self.tp_password_confirma(), fg_color='green', hover_color='green')
        button_ok.place(relx=0.18, rely=0.7)
        button_cancel=CTkButton(self.tp_password, text='Cancelar', font=self.tp_0_fonte_padrao_bold, height = 50, command=lambda:self.tp_password_cancel(), fg_color='green', hover_color='green')
        button_cancel.place(relx=0.57, rely=0.7)

        self.tp_password.after(100, self.tp_password_entry.focus_set)
        self.tp_password.bind('<Return>', lambda event: button_ok.invoke())
        self.tp_password.bind('<Escape>', lambda event: button_cancel.invoke())

        self.root.wait_window(self.tp_password)

    def tp_password_confirma(self):
        senha_inserida = self.tp_password_entry.get()
        if senha_inserida == '0805':
            self.tp_password_feedback = True
            self.fechar_tp_password()
        else:
            self.entry_sinalizer.place(relx=0.5, rely=0.5, anchor='n')

    def tp_password_cancel(self):
        yon = self.get_yes_or_not(self.tp_password, 'Calcelar a inserção da senha?')
        if yon:
            self.fechar_tp_password()
    
    def fechar_tp_password(self):
        if self.tp_password:
            self.tp_password.destroy()

    def abrir_interface_root(self):
        #Header
        logotipo = CTkImage(light_image=Image.open(r'images\logotipo.png'), size=(120, 120))
        self.label_title = CTkLabel(self.root, text=' CECÉU MINI MERCADO   ', font=CTkFont('helvetica', 80, 'bold'), image=logotipo, compound='right', 
        fg_color='black', text_color='white', width=self.tela_width, height=150, corner_radius=10)
        self.label_title.place(relx=0.5, rely=0, anchor='n')    

        #Treeview para exibir a lista de produtos
        colunas_treeview = ('Código', 'Item', 'Valor Unitário', 'Quantidade', 'Total')
        self.treeview = ttk.Treeview(self.root, columns=colunas_treeview, show='headings',height=20)
        self.treeview.place(relx=0.05, rely=0.23)
        self.treeview.column('Código', width=70, anchor=CENTER)
        self.treeview.column('Item', width=350, anchor=CENTER)
        self.treeview.column('Valor Unitário', width=120, anchor=CENTER)
        self.treeview.column('Quantidade', width=100, anchor=CENTER)
        self.treeview.column('Total', width=120, anchor=CENTER)
        self.treeview.heading('Código', text='CÓD.')
        self.treeview.heading('Item', text='ITEM')
        self.treeview.heading('Valor Unitário', text='VALOR ÚNIT')
        self.treeview.heading('Quantidade', text='QUANT.')
        self.treeview.heading('Total', text='TOTAL')

        #Entry do codbar frame
        ilus_codbar = CTkImage(light_image=Image.open(r'images\codbar_ilus.png'), size=(30, 30))
        label_ilust_codbar = CTkLabel(self.root, image=ilus_codbar, text='')
        label_ilust_codbar.place(relx=0.05, rely=0.87)

        self.root_entry_codbar = CTkEntry(self.root, width=700, height=35, border_color='green')
        self.root_entry_codbar.place(relx=0.08, rely=0.87)
        self.root_entry_codbar.focus_force()

        #Frame preço unitário
        self.frame_0 = CTkFrame(self.root, width=400, height=200, fg_color='white', corner_radius=10)
        self.frame_0.place(relx=0.65,rely=0.23)
        self.wg_0 = CTkLabel(self.frame_0, text='PREÇO UNIT.', font=CTkFont('arial', 35, 'bold'))
        self.wg_0.place(relx=0.5,rely=0.02, anchor='n' )
        self.frame_0_label_0 = CTkLabel(self.frame_0, text='0,00', font=CTkFont('courier', 80, 'bold'))
        self.frame_0_label_0.place(relx=0.5,rely=0.4, anchor='n' )

        #Frame preço total
        self.frame_1 = CTkFrame(self.root, width=400, height=200, fg_color='white', corner_radius=10)
        self.frame_1.place(relx=0.65,rely=0.55)
        self.frame_1_wg_0 = CTkLabel(self.frame_1,text='SUBTOTAL', font=CTkFont('arial', 35, 'bold'))
        self.frame_1_wg_0.place(relx=0.5,rely=0.02, anchor='n' )
        self.frame_1_label_0 = CTkLabel(self.frame_1, text='0,00', font=CTkFont('courier new', 80, 'bold'))
        self.frame_1_label_0.place(relx=0.5,rely=0.4, anchor='n' )

        #frame status atual
        self.root_frame_2 = CTkFrame(self.root, width=400, height=35, fg_color='transparent')
        self.root_frame_2.place(relx=0.65, rely=0.87)
        self.root_frame_2_label_status = CTkLabel(self.root_frame_2, text ='Aguardando Código de barras...',font=CTkFont('arial', 20, 'bold'))
        self.root_frame_2_label_status.place(relx=0.5, rely=0.02, anchor='n' )

        #footer frame
            #footer config
        self.footer_fonte = CTkFont('helvética', 10, 'bold')
        self.footer_width = self.root.winfo_width()
        self.footer_height = 30
        self.y_cordinate = self.root.winfo_height()-self.footer_height
        self.footer_frame = CTkFrame(self.root, width=self.footer_width, height=self.footer_height, fg_color='green')
        self.footer_frame.place(relx=0, y=self.y_cordinate)
            #textos do footer
        self.footer_frame_label_0 = CTkLabel(self.footer_frame, text='F1 - Cadastrar Mercadoria     F2 - Remover item da compra     F3 - Finalizar Compra     F4 - Buscar Mercadoria     F5 - Cadastrar Cliente     F6 - Fiar Compra     F7 - Buscar Fiação     F8 - Registrar Sangria    F9 - Gaveta     F12 - Fechar Caixa', 
        font=CTkFont('arial', 12, 'bold'))
        self.footer_frame_label_0.place(relx=0.01)
        self.footer_frame_label = CTkLabel(self.root, text='RayTec Soluções em Software - Todos Direitos Reservados 2024 ®')
        self.footer_frame_label.place(relx=0.7, rely=0.91)

        #Teclas Config
        self.root.bind('<F1>', lambda event: self.abrir_janela_cadastro_mercadoria())
        self.root.bind('<F2>', lambda event: self.handle_delete_row_from_treeview())
        self.root.bind('<F3>', lambda event: self.finalizar_compra())
        self.root.bind('<F4>', lambda event: self.abrir_tp_3())
        self.root.bind('<F5>', lambda event: self.abrir_tp_5())
        self.root.bind('<F6>', lambda event: self.abrir_tp_6())
        self.root.bind('<F7>', lambda event: self.abrir_tp_7())
        self.root.bind('<F8>', lambda event: self.abrir_tp_9())
        self.root.bind('<F9>', lambda event: self.abrir_gaveta())
        self.root.bind('<F11>', lambda event: self.abrir_tp_password(self.root))
        self.root.bind('<F12>', lambda event: self.abrir_tp_8())
        self.root.bind('<Escape>', lambda event: self.cancelar_compra())
        self.root_entry_codbar.bind('<Return>', lambda event: self.handle_busca_por_produto_by_codbar())
        self.treeview.bind('<Return>', lambda event: self.remove_item_selecionado())

        #setando o foco
        self.root.after(100, self.root_entry_codbar.focus_set)

    def imprimir_notas(self, text):
        com_port = 'COM2'  # Ajuste a porta conforme necessário
        baud_rate = 9600
        try:
            with serial.Serial(com_port, baud_rate, timeout=1) as printer:
                # Configurações da impressora
                printer.write(b'\x1B\x21\x00')  # Normal size
                printer.write(text.encode('utf-8'))  # Envia o texto para imprimir
                printer.write(b'\n')  # Quebra de linha
                printer.write(b'\x1D\x56\x41\x00')  # Corte do papel
                print("Nota impressa com sucesso.")
        except Exception as e:
            print(f"Erro ao imprimir a nota: {e}")

    def imprimir_cupom(self, itens, payments ,total_geral, troco):
        try:
            nota = []
        
            # Cabeçalho
            nota.append("***** Ceceu Mini Mercado *****")
            nota.append("Data: " + time.strftime("%d/%m/%Y %H:%M"))
            nota.append("************************")
            nota.append("\nItem            Qtde   Valor Unit   Total")
            nota.append("------------------------------------------")
            
            # Itens da venda
            for item in itens:
                descricao = item['product_name'][:15]
                quantidade = helper.format_to_float(item['quantity'])
                preco_unitario = helper.format_to_float(item['price'])
                total_item = quantidade * preco_unitario
                nota.append(f"{descricao:<12}   {int(quantidade):<8} R${preco_unitario:<10.2f} R${total_item:.2f}")
            
            nota.append("------------------------------------------")
            nota.append("Forma Pgmt     Valor Pago")
            nota.append("------------------------------------------")

            #forms pgmt
            for payment in payments:
                metodo = payment['method']
                if metodo != 'Dinheiro':
                    if metodo == 'Débito':
                        metodo = 'Cartao Deb.'
                    else:
                        metodo = 'Cartao Cred.'
                    amount = payment['amount']
                else:
                    amount = payment['valor_pago']
                troco = payment['troco']
                nota.append(f'         {metodo:<15} R${helper.format_to_float(amount):<10.2f}')

            nota.append("------------------------------------------")
            nota.append(f"Total Geral: R${helper.format_to_float(total_geral):<12.2f}")
            nota.append(f'Troco: R${troco:<12.2f}')
            nota.append("\nObrigado pela preferencia!")
            nota.append("************************")
            
            self.imprimir_notas("\n".join(nota))
        except Exception as e:
            CTkMessagebox(self.root, message=f'Erro ao imprimir cupom: {e}', icon='cancel', title='Erro')

    def cancelar_compra(self):
        if self.treeview.get_children():
            if self.root.focus_get() == self.treeview:
                self.cancel_handle_delete_row_from_treeview()
            else:
                yon_0 = self.get_yes_or_not(self.root, f'Confirmar o cancelamnto da compra?')
                if yon_0:
                    self.reset_root()
        else:
            CTkMessagebox(self.root, message=f'Nenhum item foi adicionado à compra.', icon='warning', title='Atenção')



    def handle_busca_por_produto_by_codbar(self):
        codbar_inserido = self.root_entry_codbar.get().strip()
        try:
            if '.' in codbar_inserido:#o programa entende aqui quando o usuario está utilizando produto genérico
                #valindando o multiplicador
                multiplicador, valor = codbar_inserido.split('.', 1)
                print(multiplicador, valor)
                if multiplicador.isdigit() and int(multiplicador) > 0:
                    #validando o valor inserido
                    try:
                        valor = valor.replace(',', '.')
                        float(valor)
                        feedback = list(backend.get_product_by_barcode('0000000000000'))
                        feedback[7] = valor
                        self.insert_row_into_treeview(feedback, quantidade=multiplicador)
                    except Exception as e:
                        CTkMessagebox(self.root, message=f'Valor do produto genérico não válido', icon='cancel', title='Erro')
                        print(e)
                        return
                else:
                    CTkMessagebox(self.root, message=f'O múltiplicador deve ser um NÚMERO INTEIRO.', icon='cancel', title='Erro')
                    return
            elif '*' in codbar_inserido:#o programa entende aqui quando o usuario está utilizando multiplicador
                multiplicador, codbar_inserido = codbar_inserido.split('*')
                #validacao do multiplicardor
                if multiplicador.isdigit() and int(multiplicador) > 0:
                    #validacao do codbar
                    if codbar_inserido.isdigit():
                        print(codbar_inserido)
                        feedback = backend.get_product_by_barcode(codbar_inserido)
                        if not feedback:     
                            self.root_entry_codbar.delete(0, END)
                            CTkMessagebox(self.root, message=f'Código de barras NÃO encontrado.', icon='cancel', title='Erro')
                        else:
                            self.insert_row_into_treeview(feedback, quantidade=multiplicador)
                    else:
                        self.root_entry_codbar.delete(0, END)
                        CTkMessagebox(self.root, message=f'Código de barras inválido.', icon='cancel', title='Erro')
                else:
                    self.root_entry_codbar.delete(0, END)
                    CTkMessagebox(self.root, message=f'O múltiplicador deve ser um NÚMERO INTEIRO.', icon='cancel', title='Erro')
                    return
            else:
                if codbar_inserido.isdigit() or codbar_inserido == '0000000000000':
                    feedback = backend.get_product_by_barcode(codbar_inserido)
                    if not feedback:     
                        self.root_entry_codbar.delete(0, END)
                        CTkMessagebox(self.root, message=f'Código de barras NÃO encontrado.', icon='cancel', title='Erro')
                    else:
                        self.insert_row_into_treeview(feedback)
                elif codbar_inserido.strip() == None:
                    CTkMessagebox(self.root, message=f'Código de barras NÃO inserido.', icon='cancel', title='Erro')   
                else:
                    self.root_entry_codbar.delete(0, END)
                    CTkMessagebox(self.root, message=f'Código de barras inválido.', icon='cancel', title='Erro')
        except Exception as e:
            self.root_entry_codbar.delete(0, END)
            CTkMessagebox(self.root, message=f'Erro ao buscar a mercadoria', icon='cancel', title='Erro*')
            traceback.print_exc()  # Imprime o traceback completo

        finally:
            self.root.after(100, self.root_entry_codbar.focus_set)
            

    def insert_row_into_treeview(self, feedback, quantidade=1):
        index = self.get_treeview_itens_number()+1
        row = helper.formatar_row_para_treeview_da_root(feedback, index, quantidade)
        self.treeview.insert('','end', values=row)
        self.lista_product_ids.append(feedback[0])
        self.frame_0_label_0.configure(text=helper.format_to_moeda(row[2]))
        #atualizando o subtotal
        self.somar_ao_subtotal(helper.format_to_float(row[-1]))
        self.root_entry_codbar.delete(0, END)


    def handle_delete_row_from_treeview(self):
        # Verifica se a Treeview não está vazia
        if self.treeview.get_children():
            self.treeview.bind('<Escape>', lambda event: self.cancel_handle_delete_row_from_treeview())
            self.root_frame_2_label_status.configure(text='Selecione o item a ser removido.')
            self.root_entry_codbar.configure(state='disabled')
            # Foca na Treeview
            self.treeview.focus_set()
            # Seleciona o primeiro item
            first_item = self.treeview.get_children()[-1]
            self.treeview.selection_set(first_item)
            # Move o foco para o item selecionado
            self.treeview.focus(first_item)
            #apos isso o ENTER acionara a funcao remove_item_selecionado
        else:
            CTkMessagebox(self.root, message=f'Nenhum item foi adicionado à compra.', icon='warning', title='Atenção')

    def cancel_handle_delete_row_from_treeview(self):
        selected_item = self.treeview.selection()
        self.treeview.selection_remove(selected_item)
        #reabilitar e foca o codbar entry
        self.root_entry_codbar.configure(state='normal')
        self.root.after(100, self.root_entry_codbar.focus_set)
        #reescrever o status label
        self.root_frame_2_label_status.configure(text='Aguardando código de barras...')

    def remove_item_selecionado(self):
        selected_item = self.treeview.selection()
        item_values = self.treeview.item(selected_item)['values']
        if selected_item:
            yon_0 = self.get_yes_or_not(self.root, f'Confirmar exclusão do item: {item_values[1]}')
            if yon_0:
                self.subtrair_do_subtotal(item_values[-1])
                self.treeview.delete(selected_item)#deleta da treeview
                removed_item_id = self.lista_product_ids.pop(int(item_values[0])-1)#deleta da lista de products_ids
                print(f'Item excluido da treeview: {selected_item}, product_id:{removed_item_id}')
                #atualiza o valor unit
                self.update_valor_unit_label()
                #aproveita a funcao abaixo para reverter os efeitos do f'sistema remover item da lista de compras
                self.cancel_handle_delete_row_from_treeview()            
        else:
            CTkMessagebox(self.root, message=f'Nenhum item selecionado para exclusão', icon='warning', title='Atenção')
            #aproveita a funcao abaixo para reverter os efeitos do f'sistema remover item da lista de compras
            self.cancel_handle_delete_row_from_treeview()  

    def subtrair_do_subtotal(self, valor):
        self.new_subtotal = helper.format_to_float(self.current_subtotal) - helper.format_to_float(valor)
        if abs(self.new_subtotal) < 1e-10:
            self.new_subtotal = 0.0
        self.frame_1_label_0.configure(text=helper.format_to_moeda(self.new_subtotal))
        self.current_subtotal = self.new_subtotal

    def somar_ao_subtotal(self, valor):
        self.new_subtotal = helper.format_to_float(self.current_subtotal) + helper.format_to_float(valor)
        if abs(self.new_subtotal) < 1e-10:
            self.new_subtotal = 0.0
        self.frame_1_label_0.configure(text=helper.format_to_moeda(self.new_subtotal))
        self.current_subtotal = self.new_subtotal

    def get_treeview_itens_number(self):
        items_len = len(self.treeview.get_children())    
        return items_len

    def update_valor_unit_label(self):
        print(self.get_treeview_itens_number())
        if self.get_treeview_itens_number() > 0:
            last_item = self.treeview.get_children()[-1]
            last_unit_value = self.treeview.item(last_item)['values'][-3]
            self.frame_0_label_0.configure(text=helper.format_to_moeda(last_unit_value))
        else:
            self.frame_0_label_0.configure(text=helper.format_to_moeda(0))

    # TOPLEVEL 0    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>   JANELA DE CADASTRO DE MERCADORIA 

    def abrir_janela_cadastro_mercadoria(self, event=None):
        #cond que verifica se a janela ja existe antes de abri-la novamente
        if self.tp_0 is not None:
            print('A janela não pode ser aberta pois já existe')
            return

        ilust_titlo = CTkImage(light_image=Image.open(r'images\ilustracao_registro_mercadoria.png'), size=(100, 100))

        #janela toplevel para cadastro de produtos
        self.tp_0 = CTkToplevel(self.root)
        self.tp_0.title('Cadastro de Produto')
        self.tp_0.protocol('WM_DELETE_WINDOW', self.fechar_janela_cadastro)
        self.tp_0.resizable(False, False)
        self.tp_0_width = 1200
        self.tp_0_height = 650
        self.tp_0_x = self.root.winfo_width()//2 - self.tp_0_width//2
        self.tp_0_y = self.root.winfo_height()//2 - self.tp_0_height//2
        self.tp_0.geometry(f'{self.tp_0_width}x{self.tp_0_height}+{self.tp_0_x}+{self.tp_0_y}')
        self.tp_0.attributes('-topmost', 'true')
        self.check_cod_block = False
        self.tp_0_validate_block = False
        self.first_enter = False

        self.tp_0_label_titlo = CTkLabel(self.tp_0, text='Registro de Mercadoria:', font=CTkFont('arial', 35, 'bold'), image=ilust_titlo, compound='left')
        self.tp_0_label_titlo.place(relx = 0.5, rely=0.02, anchor='n')

        self.tp_0_label_1 = CTkLabel(self.tp_0, text='Cód. barras:', font=self.tp_0_fonte_padrao_bold)
        self.tp_0_label_1.place(relx=0.02, rely=0.22)
        self.tp_0_entry_1 = CTkEntry(self.tp_0, font=self.tp_0_fonte_padrao, width=400, height=50)
        self.tp_0_entry_1.place(relx=0.13, rely=0.20)
        self.tp_0_entry_1_sinalizer = CTkLabel(self.tp_0 ,text_color='red')
        self.tp_0_ignore_enter = False
        self.tp_0_entry_1.bind('<KeyRelease>', self.check_cod)

        self.tp_0_label_2 = CTkLabel(self.tp_0, text='Descrição:', font=self.tp_0_fonte_padrao_bold)
        self.tp_0_label_2.place(relx=0.02, rely=0.35)
        self.tp_0_entry_2 = CTkEntry(self.tp_0, font=self.tp_0_fonte_padrao, width=400, height=50)
        self.tp_0_entry_2.place(relx=0.13, rely=0.33)
        self.tp_0_entry_2_sinalizer = CTkLabel(self.tp_0 ,text_color='red')

        self.tp_0_label_3 = CTkLabel(self.tp_0, text='NCM:', font=self.tp_0_fonte_padrao_bold)
        self.tp_0_label_3.place(relx=0.02, rely=0.48)
        self.tp_0_entry_3 = CTkEntry(self.tp_0, font=self.tp_0_fonte_padrao, width=400, height=50)
        self.tp_0_entry_3.place(relx=0.13, rely=0.46)
        self.tp_0_entry_3_sinalizer = CTkLabel(self.tp_0 ,text_color='red')

        self.tp_0_label_4 = CTkLabel(self.tp_0, text='NCM DESC:', font=self.tp_0_fonte_padrao_bold)
        self.tp_0_label_4.place(relx=0.02, rely=0.61)
        self.tp_0_entry_4 = CTkEntry(self.tp_0, font=self.tp_0_fonte_padrao, width=400, height=50)
        self.tp_0_entry_4.place(relx=0.13, rely=0.59)
        self.tp_0_entry_4_sinalizer = CTkLabel(self.tp_0 ,text_color='red')

        self.tp_0_label_9 = CTkLabel(self.tp_0, text='Marca:', font=self.tp_0_fonte_padrao_bold)
        self.tp_0_label_9.place(relx=0.02, rely=0.74)
        self.tp_0_entry_9 = CTkEntry(self.tp_0, font=self.tp_0_fonte_padrao, width=400, height=50)
        self.tp_0_entry_9.place(relx=0.13, rely=0.72)
        self.tp_0_entry_9_sinalizer = CTkLabel(self.tp_0 ,text_color='red')

        #COLUMN 2

        self.tp_0_label_5 = CTkLabel(self.tp_0, text='Nome:', font=self.tp_0_fonte_padrao_bold)
        self.tp_0_label_5.place(relx=0.49, rely=0.22)
        self.tp_0_entry_5 = CTkEntry(self.tp_0, font=self.tp_0_fonte_padrao, width=400, height=50)
        self.tp_0_entry_5.place(relx=0.60, rely=0.20)
        self.tp_0_entry_5_sinalizer = CTkLabel(self.tp_0 ,text_color='red')

        self.tp_0_label_6 = CTkLabel(self.tp_0, text='Preço:', font=self.tp_0_fonte_padrao_bold)
        self.tp_0_label_6.place(relx=0.49, rely=0.35)
        self.tp_0_entry_6 = CTkEntry(self.tp_0, font=self.tp_0_fonte_padrao, width=400, height=50)
        self.tp_0_entry_6.place(relx=0.60, rely=0.33)
        self.tp_0_entry_6_sinalizer = CTkLabel(self.tp_0 ,text_color='red')

        self.tp_0_label_7 = CTkLabel(self.tp_0, text='Quantidade:', font=self.tp_0_fonte_padrao_bold)
        self.tp_0_label_7.place(relx=0.49, rely=0.48)
        self.tp_0_entry_7 = CTkEntry(self.tp_0, font=self.tp_0_fonte_padrao, width=400, height=50)
        self.tp_0_entry_7.place(relx=0.60, rely=0.46)
        self.tp_0_entry_7_sinalizer = CTkLabel(self.tp_0 ,text_color='red')

        self.tp_0_label_8 = CTkLabel(self.tp_0, text='Origem:', font=self.tp_0_fonte_padrao_bold)
        self.tp_0_label_8.place(relx=0.49, rely=0.61)
        self.tp_0_entry_8 = CTkEntry(self.tp_0, font=self.tp_0_fonte_padrao, width=400, height=50)
        self.tp_0_entry_8.place(relx=0.60, rely=0.59)
        self.tp_0_entry_8_sinalizer = CTkLabel(self.tp_0 ,text_color='red')

        self.tp_0_label_10 = CTkLabel(self.tp_0, text='Data Venc.:', font=self.tp_0_fonte_padrao_bold)
        self.tp_0_label_10.place(relx=0.49, rely=0.74)
        self.tp_0_entry_10 = CTkEntry(self.tp_0, font=self.tp_0_fonte_padrao, width=400, height=50)
        self.tp_0_entry_10.place(relx=0.60, rely=0.72)
        self.tp_0_entry_10_sinalizer = CTkLabel(self.tp_0 ,text_color='red')

        #campo para botão de registro
        self.tp_0_botao_registrar_mercadoria = CTkButton(self.tp_0, width=200 ,height=50,text='Registrar', font=self.tp_0_fonte_padrao_bold, 
        command=lambda: self.validar_dados_do_registro_de_mercadorias(), text_color='black', fg_color='green', hover_color='green')
        self.tp_0_botao_registrar_mercadoria.place(relx=0.5, rely=0.95, anchor='s')

        self.tp_0.after(100, self.tp_0_entry_1.focus_set)

        #vinculações de teclas
        self.tp_0.bind('<Escape>', lambda event: self.fechar_janela_cadastro())
        self.tp_0.bind('<Return>', lambda event: self.tp_0_botao_registrar_mercadoria.invoke())

    def check_cod(self, event=None):
        def insert_into_entrys():
            self.tp_0_entry_2.insert(0, cfm[0])
            self.tp_0_entry_3.insert(0, cfm[1])
            self.tp_0_entry_4.insert(0, cfm[2])
            self.tp_0_entry_9.insert(0, cfm[3])

        def clear_entrys():
            self.tp_0_entry_2.delete(0, END)
            self.tp_0_entry_3.delete(0, END)
            self.tp_0_entry_4.delete(0, END)
            self.tp_0_entry_9.delete(0, END)   

        codbar_inserido = self.tp_0_entry_1.get().strip()
        if codbar_inserido.isdigit() and len(codbar_inserido) == 13:
            if self.check_cod_block:
                return
            self.check_cod_block = True
            try:
                clear_entrys()
                cfm = backend.get_product_by_barcode(codbar_inserido)
                if cfm: #se ja existe o codbar ele da return
                    CTkMessagebox(self.root, message=f'Produto já cadastrado: {cfm[2].upper()}', icon='warning', title='Atenção')
                    self.tp_0_entry_1.delete(0, END)
                    return
                cfm = api.get_product_data_from_cosmos_by_ean(codbar_inserido)
                if cfm:
                    insert_into_entrys()
                else:
                    raise Exception('Erro ao capturar os dados do produto apartir CodBar.')
            except Exception as e:
                CTkMessagebox(self.tp_0, title='Erro.', message=f'Erro: {e}. Considere contatar a assistência: {self.contato}')
            finally:    
                self.check_cod_block = False

    def validar_dados_do_registro_de_mercadorias(self):
        if not self.first_enter:
            self.first_enter = True
            return
        if self.tp_0_validate_block:
            return
        try:
            self.tp_0_validate_block=True
            self.tp_0_clear_sinalizers()
            codbar_inserido = self.tp_0_entry_1.get().strip()
            if not codbar_inserido:
                self.tp_0_entry_1_sinalizer.configure(text='O código de barras não foi inserido.')
                self.tp_0_entry_1_sinalizer.place(relx=0.13, rely=0.28)
                return
            elif not codbar_inserido.isdigit():
                self.tp_0_entry_1_sinalizer.configure(text='O código de barras deve ser numérico.')
                self.tp_0_entry_1_sinalizer.place(relx=0.13, rely=0.28)
                return
            elif len(codbar_inserido) not in (8, 13):
                self.tp_0_entry_1_sinalizer.configure(text='O código de barras deve conter 13 dígitos.')
                self.tp_0_entry_1_sinalizer.place(relx=0.13, rely=0.28)
                return
            desc_inserida = self.tp_0_entry_2.get().strip()
            if not desc_inserida:
                self.tp_0_entry_2_sinalizer.configure(text='A descrição da mercadoria não foi inserida.')
                self.tp_0_entry_2_sinalizer.place(relx=0.13, rely=0.41)
                return
            elif desc_inserida.isdigit():
                self.tp_0_entry_2_sinalizer.configure(text='A descrição da mercadoria deve conter letras.')
                self.tp_0_entry_2_sinalizer.place(relx=0.13, rely=0.41)
                return
            ncm_inserido = self.tp_0_entry_3.get().strip()
            if not ncm_inserido:
                self.tp_0_entry_3_sinalizer.configure(text='O NCM da mercadoria não foi inserido.')
                self.tp_0_entry_3_sinalizer.place(relx=0.13, rely=0.54)
                return
            elif not ncm_inserido.isdigit():
                self.tp_0_entry_3_sinalizer.configure(text='O NCM deve ser numérico.')
                self.tp_0_entry_3_sinalizer.place(relx=0.13, rely=0.54)
                return
            elif len(ncm_inserido) != 8:
                self.tp_0_entry_3_sinalizer.configure(text='O NCM da mercadoria deve conter 8 dígitos.')
                self.tp_0_entry_3_sinalizer.place(relx=0.13, rely=0.54)
                return
            ncm_desc_inserido = self.tp_0_entry_4.get().strip()
            if ncm_desc_inserido:
                if ncm_desc_inserido.isdigit():
                    self.tp_0_entry_4_sinalizer.configure(text='O NCM deve conter letras.')
                    self.tp_0_entry_4_sinalizer.place(relx=0.13, rely=0.67)
                    return
            marca_inserida = self.tp_0_entry_9.get().strip()
            if marca_inserida:
                if ncm_desc_inserido.isdigit():
                    self.tp_0_entry_9_sinalizer.configure(text='O nome da marca deve conter letras.')
                    self.tp_0_entry_9_sinalizer.place(relx=0.13, rely=0.8)
                    return
            nome_inserido = self.tp_0_entry_5.get().strip()
            if not nome_inserido:
                self.tp_0_entry_5_sinalizer.configure(text='O nome da mercadoria não foi inserido.')
                self.tp_0_entry_5_sinalizer.place(relx=0.60, rely=0.28)
                return
            elif nome_inserido.isdigit():
                self.tp_0_entry_5_sinalizer.configure(text='O nome da mercadoria deve conter letras.')
                self.tp_0_entry_5_sinalizer.place(relx=0.60, rely=0.28)        
                return
            preco_inserido = self.tp_0_entry_6.get().replace(',', '.').strip()
            if not preco_inserido:
                self.tp_0_entry_6_sinalizer.configure(text='O preco não foi inserido')
                self.tp_0_entry_6_sinalizer.place(relx=0.60, rely=0.41)
                return
            if preco_inserido:            
                try:
                    if float(preco_inserido) < 0:
                        raise Exception
                except:
                    self.tp_0_entry_6_sinalizer.configure(text='Preço inválido')
                    self.tp_0_entry_6_sinalizer.place(relx=0.60, rely=0.41)
                    return
            quantidade_inserida = self.tp_0_entry_7.get().strip()
            if quantidade_inserida:
                try:
                    quantidade_inserida = int(quantidade_inserida)
                    if quantidade_inserida < 0:
                        raise ValueError
                except:
                    self.tp_0_entry_7_sinalizer.configure(text='A quantidade deve ser um numero inteiro.')
                    self.tp_0_entry_7_sinalizer.place(relx=0.60, rely=0.54)
                    return
            origem_inserida = self.tp_0_entry_9.get().strip()
            data_venc_inserida = self.tp_0_entry_10.get().strip()
            if data_venc_inserida:
                cfm_0 = helper.check_date(data_venc_inserida)
                if not cfm_0[0]:
                    self.tp_4_entry_10_sinalizer.configure(text=f'{cfm_0[1]}')
                    self.tp_4_entry_10_sinalizer.place(relx=0.60, rely=0.8)
                    return
            cfm = self.get_yes_or_not(self.tp_4)
            if cfm:
                cfm_2 = backend.insert_product((codbar_inserido, desc_inserida, ncm_inserido, ncm_desc_inserido, marca_inserida, nome_inserido, preco_inserido, quantidade_inserida, origem_inserida, data_venc_inserida))
                if cfm_2:
                    CTkMessagebox(self.tp_0, message="Produto cadastrado com sucesso!", icon='check', title='')
                    self.fechar_janela_cadastro()
                else:
                    CTkMessagebox(self.tp_0, title='Erro.', message=f'Erro ao registrar mercadoria: {e}. Considere contatar a assistência: {self.contato}.')
            else:
                pass
        except Exception as e:
            print(e)
            CTkMessagebox(self.tp_0, title='Erro.', message=f'Erro ao validar os dados inseridos: {e}. Considere contatar a assistência: {self.contato}')
        finally:
            self.tp_0_validate_block = False

    def tp_0_clear_sinalizers(self):
        #removendo os sinalizers labels
        self.tp_0_entry_1_sinalizer.place_forget()
        self.tp_0_entry_2_sinalizer.place_forget()
        self.tp_0_entry_3_sinalizer.place_forget()
        self.tp_0_entry_4_sinalizer.place_forget()
        self.tp_0_entry_9_sinalizer.place_forget()
        self.tp_0_entry_5_sinalizer.place_forget()
        self.tp_0_entry_6_sinalizer.place_forget()
        self.tp_0_entry_7_sinalizer.place_forget()
        self.tp_0_entry_8_sinalizer.place_forget()
        self.tp_0_entry_10_sinalizer.place_forget()

    def handle_product_registration(self, barcode, name, price, quantity, origem):
        feedback = backend.insert_product(barcode, name, price, quantity, origem) 
        if feedback == None:
            CTkMessagebox(self.tp_0, message="Produto cadastrado com sucesso!", icon='check', title='')
        elif feedback == 'Erro não identificado':
            CTkMessagebox(self.tp_0, message=feedback, icon='cancel', title='Erro')
        else:
            CTkMessagebox(self.tp_0, message=f'Código de barras já está cadastro. Produto: {feedback[2].capitalize()}', icon='cancel', title='')

    def tp_0_widgets_clear(self):
        #clearning entrys 
        self.tp_0_entry_codigo_barras.delete(0, END)
        self.tp_0_entry_produto.delete(0, END)
        self.tp_0_entry_preco.delete(0, END)
        self.tp_0_entry_quantidade.delete(0,END)
        self.tp_0_entry_origem.delete(0, END)

    def fechar_janela_cadastro(self):
        if self.tp_0:
            self.tp_0.destroy()
            self.tp_0 = None

    # TOPLEVEL 1    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>   JANELA SELECIONAR FORMA DE PAGAMENTO 

    def finalizar_compra(self):  
        #verifica se a treeview esta vazia
        if self.get_treeview_itens_number() == 0:
            CTkMessagebox(self.root, message=f'Nenhum item foi adicionado à compra.', icon='warning', title='Atenção')
            return 
        
        x = self.abrir_tp_1_0()


    def abrir_tp_1_0(self):
        self.root_frame_2_label_status.configure(text='Finalizando Compra...')
        #janela toplevel para cadastro de produtos
        self.tp_1 = CTkToplevel(self.root)
        self.tp_1.title('Selecionar Forma de Pagamento')
        self.tp_1.protocol('WM_DELETE_WINDOW', self.fechar_tp_1)
        self.tp_1_width = 500
        self.tp_1_height = 300
        self.tp_1_x = self.root.winfo_width()//2 - self.tp_1_width//2   #essa e algumas abaixo, sao linhas que centralizam o tp na root
        self.tp_1_y = self.root.winfo_height()//2 - self.tp_1_height//2
        self.tp_1.geometry(f'{self.tp_1_width}x{self.tp_1_height}+{self.tp_1_x}+{self.tp_1_y}')
        self.tp_1.resizable(False, False)
        self.tp_1.attributes('-topmost', 'true')
        self.tp_1_fonte_padrao_bold = CTkFont('arial', 20, 'bold')
        self.tp_1_fonte_padrao = CTkFont('arial', 30)
        self.tp_1.grab_set()

        self.total_restante = helper.format_to_float(self.frame_1_label_0.cget('text'))
        self.payments = []
        self.troco = 0

        #widgets config
        
        self.tp_1_label_titlo_seg_button = CTkLabel(self.tp_1, text='Forma de Pagamento:', font=self.tp_1_fonte_padrao_bold)
        self.tp_1_label_titlo_seg_button.place(relx = 0.5, rely=0.05, anchor='n')

        self.formas_pgmt_ativas_cap = tuple(form_pgmt.capitalize() for form_pgmt in self.formas_pgmt_ativas)
        self.tp_1_form_pgmt_seg_button =CTkSegmentedButton(self.tp_1, values=self.formas_pgmt_ativas_cap, font=self.tp_1_fonte_padrao, text_color='black', fg_color='white', unselected_color='white', unselected_hover_color='white', selected_color='green', selected_hover_color='green')
        self.tp_1_form_pgmt_seg_button.place(relx=0.5, rely=0.2, anchor='n')
        self.tp_1_form_pgmt_seg_button.set(self.formas_pgmt_ativas_cap[0])

        self.tp_1_valor_entry = CTkEntry(self.tp_1, font=CTkFont('courier', 50, 'bold'), width=250)
        self.tp_1_valor_entry.place(relx=0.5, rely=0.5, anchor='n')
        self.tp_1_valor_entry_sinalizer = CTkLabel(self.tp_1, text_color='red', text='Insira um valor válido')

        self.tp_1_valor_restante_titlo = CTkLabel(self.tp_1, text='TOTAL: ', font=self.tp_1_fonte_padrao_bold)
        self.tp_1_valor_restante_titlo.place(relx=0.25, rely=0.85, anchor='n')
        self.tp_1_valor_restante = CTkLabel(self.tp_1, font=CTkFont('courier', 50, 'bold'), text=self.total_restante)
        self.tp_1_valor_restante.place(relx=0.5, rely=0.8, anchor='n')

        #ajuste de foco ao abrir
        self.tp_1.after(100, self.tp_1_valor_entry.focus_set)
        
        #block de entrada de dados
        self.root_entry_codbar.configure(state='disabled')

        #vinculação de teclas
        self.tp_1.bind('<Escape>', lambda event: self.cancelar_finalizacao_compra(self.tp_1))
        self.tp_1.bind('<Return>', lambda event: self.validate_tp_1_0())
        self.tp_1.bind('<Right>', lambda event: self.move_to_next_form_pgmt())
        self.tp_1.bind('<Left>', lambda event: self.move_to_previous_form_pgmt())

    def validate_tp_1_0(self):#forms pgmt
        self.tp_1_valor_entry_sinalizer.place_forget()
        self.selected_form_pgmt = self.tp_1_form_pgmt_seg_button.get()
        self.valor_inserido = self.tp_1_valor_entry.get().strip().replace(',', '.').replace('-', '')
        self.abrir_gaveta_check = False
        try:
            self.valor_inserido = float(self.valor_inserido)
            if self.selected_form_pgmt == 'Dinheiro':
                if self.valor_inserido < self.total_restante:
                    CTkMessagebox(self.root, message=f'Se houver mais de uma forma de pagamento, deixe a em DINHEIRO por último.', icon='warning', title='Atenção')
                    return
            else:
                if self.valor_inserido > self.total_restante:
                    self.valor_inserido = self.total_restante
            yon_0 = self.get_yes_or_not(self.tp_1, f'Confirmar Operação? {helper.format_to_moeda(self.valor_inserido)} no {self.selected_form_pgmt}.')
            if yon_0:
                self.troco = 0
                if 'Dinheiro' == self.selected_form_pgmt:#calculador do troco
                    self.troco = self.valor_inserido - self.total_restante
                    self.abrir_gaveta_check = True
                self.payments.append({'method': self.selected_form_pgmt, 'amount': helper.format_to_float(self.valor_inserido - self.troco), 'valor_pago': self.valor_inserido, 'troco': self.troco}) 
                if helper.format_to_float(self.total_restante) - self.valor_inserido  <= float(0): #para de uma forma de pagamento
                    self.fechar_tp_1()
                    self.abrir_tp_2()#tp_2 == tp_cpf
                else: #para o caso de mais de uma forma de pagamento \ recalculo do valor restante
                    self.tp_1_valor_restante_titlo.configure(text='Restante:')
                    self.total_restante = helper.format_to_float(self.total_restante) - float(self.valor_inserido)
                    self.tp_1_valor_restante.configure(text=helper.format_to_moeda(self.total_restante))
                    self.tp_1_valor_entry.delete(0, END)
            else:
                return
        except Exception as e:#para o caso de valor inválido
            self.tp_1_valor_entry_sinalizer.place(relx=0.5, rely=0.725, anchor='n')
            CTkMessagebox(self.root, message=f'Erro ao validar forma de pagamento: {e}', icon='cancel', title='Erro')
            print({e})

    def move_to_next_form_pgmt(self):
        current_value_index = self.formas_pgmt_ativas_cap.index(self.tp_1_form_pgmt_seg_button.get())
        next_index = (current_value_index + 1) % len(self.formas_pgmt_ativas_cap)
        self.tp_1_form_pgmt_seg_button.set(self.formas_pgmt_ativas_cap[next_index])

    def move_to_previous_form_pgmt(self):
        current_value_index = self.formas_pgmt_ativas_cap.index(self.tp_1_form_pgmt_seg_button.get())
        next_index = (current_value_index - 1) % len(self.formas_pgmt_ativas_cap)
        self.tp_1_form_pgmt_seg_button.set(self.formas_pgmt_ativas_cap[next_index])

    def cancelar_finalizacao_compra(self, janela):
        yon= self.get_yes_or_not(janela, 'Cancelar a finalização da compra?')
        if yon:
            if self.tp_1:
                self.tp_1.destroy()
            if self.tp_2:
                self.tp_2.destroy()
            self.root_frame_2_label_status.configure(text='Aguardando Código de barras...')

    def fechar_tp_1(self):
        if self.tp_1:
            self.tp_1.destroy()
            self.tp_1 = None
            self.root_entry_codbar.configure(state='normal')  

    # TOPLEVEL 2    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>   JANELA INSERIR CPF

    def abrir_tp_2(self):
        #janela toplevel para cadastro de produtos
        self.tp_2 = CTkToplevel(self.root)
        self.tp_2.title('Inserir CPF')
        self.tp_2.protocol('WM_DELETE_WINDOW', self.fechar_tp_1)
        self.tp_2_width = 350
        self.tp_2_height = 250
        self.tp_2_x = self.root.winfo_width()//2 - self.tp_2_width//2   #essa e algumas abaixo, sao linhas que centralizam o tp na root
        self.tp_2_y = self.root.winfo_height()//2 - self.tp_2_height//2
        self.tp_2.geometry(f'{self.tp_2_width}x{self.tp_2_height}+{self.tp_2_x}+{self.tp_2_y}')
        self.tp_2.resizable(False, False)
        self.tp_2.attributes('-topmost', 'true')
        self.tp_2_fonte_padrao_bold = CTkFont('arial', 20, 'bold')
        self.tp_2_fonte_padrao = CTkFont('arial', 30)
        self.tp_2.grab_set()

        self.tp_2_titlo = CTkLabel(self.tp_2, text='Inserir CPF', font=self.tp_2_fonte_padrao_bold)
        self.tp_2_titlo.place(relx=0.5,rely=0.1, anchor='n')

        self.tp_2_entry = CTkEntry(self.tp_2, font=self.tp_2_fonte_padrao, width=250)
        self.tp_2_entry.place(relx=0.5,rely=0.3, anchor='n')
        self.tp_2_entry_sinalizer = CTkLabel(self.tp_2, text='CPF inválido', text_color='red')

        self.tp_2_troco_restante_titlo = CTkLabel(self.tp_2, text='TROCO:', font=self.tp_1_fonte_padrao_bold)
        self.tp_2_troco_restante_titlo.place(relx=0.2, rely=0.75, anchor='n')
        self.tp_2_troco_restante = CTkLabel(self.tp_2, font=CTkFont('courier', 50, 'bold'), text=helper.format_to_moeda(self.troco))
        self.tp_2_troco_restante.place(relx=0.6, rely=0.7, anchor='n')

        self.tp_2.after(100, self.tp_2_entry.focus_set)

        self.tp_2.bind('<Return>', lambda event: self.tp_2_validate())
        self.tp_2.bind('<Escape>', lambda event: self.cancelar_finalizacao_compra(self.tp_2))


    def tp_2_validate(self):#cpf
        self.cpf_inserido = self.tp_2_entry.get().strip()
        if self.cpf_inserido:#se haver cpf
            if self.cpf_inserido.isdigit() and len(self.cpf_inserido) == 11:
                yon = self.get_yes_or_not(self.tp_2, f'Inserir o CPF: {self.cpf_inserido} e finalizar a compra?')
                if yon:
                    self.encerrar_finzalização_da_compra()
                    self.tp_2_fechar
            else:
                self.tp_2_entry_sinalizer.place(relx=0.5,rely=0.7, anchor='n')
        else:
            yon = self.get_yes_or_not(self.tp_2, 'Finalizar a compra sem CPF?')
            if yon:
                self.encerrar_finzalização_da_compra()

    def encerrar_finzalização_da_compra(self):
        try:
            items = self.get_treeview_data()#agrupando os dados
            total = self.frame_1_label_0.cget('text')
            if self.customer_id:
                key = self.abrir_tp_password(self.tp_8)
                if self.tp_password_feedback:
                    cfm = backend.delete_oncredits_by_customer_id_and_insert_sale_into_tables(self.customer_id, items, self.payments)
                    if cfm:
                        CTkMessagebox(self.root, message=f"Os valores foram descontados da conta do cliente de id: {self.cliente_selecionado}", icon='check', title='')
                        yon = self.get_yes_or_not(self.root, 'Imprimir Cupom fiscal?')
                        if yon:
                            self.imprimir_cupom(items, self.payments, total, self.troco)
                            self.reset_root()
                        else:
                            self.reset_root()
                        if self.abrir_gaveta_check:
                            self.abrir_gaveta()
                    else:
                        CTkMessagebox(self.root, message='Erro na hora de descontar os valores da conta do cliente e registrar venda. Operação CANCELADA.', icon='cancel', title='Erro')
                else:
                    print('Senha nao aceita. operacao descontinuada.')
            else:
                feedback = backend.insert_sale_into_tables(items, self.payments)#lancar no database
                if feedback:
                    yon = self.get_yes_or_not(self.root, 'Imprimir Cupom fiscal?')
                    if yon:
                        self.imprimir_cupom(items, self.payments, total, self.troco)
                        self.reset_root()
                    else:
                        self.reset_root()
                    if self.abrir_gaveta_check:
                        self.abrir_gaveta()

        except Exception as e:
            print(e)
            CTkMessagebox(self.root, message=f'Erro na hora de finalizar compra: contate: {self.contato} ou reinicie o PDV.', icon='cancel', title='Erro')

    def reset_root(self):
        self.root_frame_2_label_status.configure(text='Aguardando Código de barras...')
        self.frame_0_label_0.configure(text='0,00')
        self.frame_1_label_0.configure(text='0,00')
        self.current_subtotal = helper.format_to_moeda(0) #subtotal atual
        self.limpar_treeview()
        self.tp_2_fechar()  
        self.fechar_tp_1()
        self.root_entry_codbar.configure(state='normal')
        self.root.after(100, self.root_entry_codbar.focus_set)
        self.customer_id = 0
        self.tp_password_feedback = False
        self.cliente_selecionado = ''

    def limpar_treeview(self):
        try:
            for i in self.treeview.get_children():
                self.treeview.delete(i)
        except:
            print('Erro na hora de limpar treeview')
            return

    def get_treeview_data(self):
        # Função para extrair os dados da Treeview
        items = []
        for index, child in enumerate(self.treeview.get_children()):#percorrendo a treeview e criando um dict para cada item
            product_id = self.lista_product_ids[index]  # Supondo que o ID do produto está na coluna 0
            product_name = self.treeview.item(child, 'values')[1].lower()  # nome do item  
            quantity = helper.format_to_float(self.treeview.item(child, 'values')[3])  # Quantidade
            price = helper.format_to_float(self.treeview.item(child, 'values')[2])  # Preço unitário
            item_id = self.treeview.item(child, 'values')[0]
            
            items.append({
                'product_id': product_id,
                'item_id': item_id,
                'product_name': product_name,
                'quantity': quantity,
                'price': price
            })
        return items

    def tp_2_fechar(self):
        if self.tp_2:
            self.tp_2.destroy()
            self.tp_2 = None

    # TOPLEVEL 3    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>   TREEVIEW BUSCA POR PRODUTOS

    def abrir_tp_3(self):
        if not self.tp_3:
            self.tp_3 = CTkToplevel(self.root)
            self.tp_3.title('Visualizar e Editar Mercadoria')
            self.tp_3.protocol('WM_DELETE_WINDOW', self.fechar_tp_3)
            self.tp_3_width = 1200
            self.tp_3_height = 600
            self.tp_3_x = self.root.winfo_width()//2 - self.tp_3_width//2   #essa e algumas abaixo, sao linhas que centralizam o tp na root
            self.tp_3_y = self.root.winfo_height()//2 - self.tp_3_height//2
            self.tp_3.geometry(f'{self.tp_3_width}x{self.tp_3_height}+{self.tp_3_x}+{self.tp_3_y}')
            self.tp_3.resizable(False, False)
            self.tp_3.attributes('-topmost', 'true')

            ilust_titlo = CTkImage(light_image=Image.open(r'images\ilustracao_pesquisa_mercadoria.png'), size=(100, 100))

            self.tp_0_label_titlo = CTkLabel(self.tp_3,  text='', image=ilust_titlo)
            self.tp_0_label_titlo.place(relx = 0.1, rely=0.05, anchor='n')

            # Entry para inserir a busca
            self.search_entry = CTkEntry(self.tp_3, width=750, height=50, placeholder_text="Digite o nome do produto...", font=self.fonte_basic, border_color='green')
            self.search_entry.place(relx=0.2,rely=0.1)
            self.search_entry.bind("<KeyRelease>", self.search_product)
            self.tp_3.after(100, self.search_entry.focus_set)
            
            # Treeview para exibir os resultados de forma tabular
            self.result_tree_columns = ('id', 'barcode','descricao', 'nome', 'price', 'quantity', 'source', 'data_vencimento')
            self.result_tree = ttk.Treeview(self.tp_3, columns=self.result_tree_columns, show="headings", height=20)
            self.result_tree.column(self.result_tree_columns[0], width=50, anchor=CENTER)
            self.result_tree.column(self.result_tree_columns[1], width=135, anchor=CENTER)
            self.result_tree.column(self.result_tree_columns[2], width=250, anchor=CENTER)
            self.result_tree.column(self.result_tree_columns[3], width=250, anchor=CENTER)
            self.result_tree.column(self.result_tree_columns[4], width=100, anchor=CENTER)
            self.result_tree.column(self.result_tree_columns[5], width=100, anchor=CENTER)
            self.result_tree.column(self.result_tree_columns[6], width=100, anchor=CENTER)
            self.result_tree.column(self.result_tree_columns[7], width=100, anchor=CENTER)
            self.result_tree.heading(self.result_tree_columns[0], text="ID", )
            self.result_tree.heading(self.result_tree_columns[1], text="Cód. Barras", )
            self.result_tree.heading(self.result_tree_columns[2], text="Descrição")
            self.result_tree.heading(self.result_tree_columns[3], text="Nome")
            self.result_tree.heading(self.result_tree_columns[4], text="Preço")
            self.result_tree.heading(self.result_tree_columns[5], text="Quantidade")
            self.result_tree.heading(self.result_tree_columns[6], text="Source")
            self.result_tree.heading(self.result_tree_columns[7], text="Data Venc.")
            self.result_tree.place(relx=0.5, rely=0.25, anchor='n')

            self.update_search_treeview()

            self.tp_3.bind('<Escape>', self.fechar_tp_3)
            self.tp_3.bind('<Double-1>', self.abrir_tp_4)

    def search_product(self, event=None):
        search_term = self.search_entry.get()
        if search_term.isdigit():   #para o caso de ser código de barras
            search_by = 'barcode'
        else:                       #para o caso de ser pelo nome
            search_by = 'descricao'
        # Limpa a Treeview antes de exibir os novos resultados
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        # Chama a função de busca no banco de dados do backend
        results = backend.search_products(search_term, search_by)
        if results:
            # Adiciona os resultados na Treeview
            for row in results:
                self.result_tree.insert('', END, values=helper.formatar_row_para_treeview_da_busca(row))
        
    def update_search_treeview(self):
        # Limpa a Treeview antes de exibir os novos resultados
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        # Chama a função de busca no banco de dados do backend
        results = backend.get_all_products()
        if results:
            # Adiciona os resultados na Treeview
            for row in results:
                self.result_tree.insert('', END, values=helper.formatar_row_para_treeview_da_busca(row))

    def fechar_tp_3(self, event=None):
        if self.tp_3:
            self.tp_3.destroy()
            self.tp_3 = None

    def abrir_tp_4(self, event=None):
        selected_item = self.result_tree.focus()
        self.item_values = self.result_tree.item(selected_item, "values")
        self.item_values = backend.get_product_by_barcode(self.item_values[1])
        if not self.item_values:
            self.search_entry.focus_set()
            return
        if self.tp_4:
            return  
        #janela toplevel para cadastro de produtos
        self.tp_4 = CTkToplevel(self.root)
        self.tp_4.title('Editar Mercadoria')
        self.tp_4.protocol('WM_DELETE_WINDOW', self.fechar_tp_4)
        self.tp_4.resizable(False, False)
        self.tp_4_width = 1200
        self.tp_4_height = 650
        self.tp_4_x = self.root.winfo_width()//2 - self.tp_4_width//2
        self.tp_4_y = self.root.winfo_height()//2 - self.tp_4_height//2
        self.tp_4.geometry(f'{self.tp_4_width}x{self.tp_4_height}+{self.tp_4_x}+{self.tp_4_y}')
        self.tp_4.attributes('-topmost', 'true')
        self.tp_4_validate_block = False
        self.first_enter = False

        ilust_titlo = CTkImage(light_image=Image.open(r'images\ilustracao_edita_mercadoria.png'), size=(100, 100))

        self.tp_4_titlo = CTkLabel(self.tp_4, text='Editar Mercadoria:', font=CTkFont('arial', 35, 'bold'), image=ilust_titlo, compound='left')
        self.tp_4_titlo.place(relx = 0.5, rely=0.02, anchor='n')

        self.tp_4_label_1 = CTkLabel(self.tp_4, text='Cód. barras:', font=self.tp_0_fonte_padrao_bold)
        self.tp_4_label_1.place(relx=0.02, rely=0.22)
        self.tp_4_entry_1 = CTkEntry(self.tp_4, font=self.tp_0_fonte_padrao, width=400, height=50)
        self.tp_4_entry_1.place(relx=0.13, rely=0.20)
        self.tp_4_entry_1.insert(0, self.item_values[1])
        self.tp_4_entry_1.configure(state='disabled')
        self.tp_4_entry_1_sinalizer = CTkLabel(self.tp_4 ,text_color='red')

        self.tp_4_label_2 = CTkLabel(self.tp_4, text='Descrição:', font=self.tp_0_fonte_padrao_bold)
        self.tp_4_label_2.place(relx=0.02, rely=0.35)
        self.tp_4_entry_2 = CTkEntry(self.tp_4, font=self.tp_0_fonte_padrao, width=400, height=50)
        self.tp_4_entry_2.place(relx=0.13, rely=0.33)
        self.tp_4_entry_2.insert(0, self.item_values[2])
        self.tp_4_entry_2_sinalizer = CTkLabel(self.tp_4 ,text_color='red')

        self.tp_4_label_3 = CTkLabel(self.tp_4, text='NCM:', font=self.tp_0_fonte_padrao_bold)
        self.tp_4_label_3.place(relx=0.02, rely=0.48)
        self.tp_4_entry_3 = CTkEntry(self.tp_4, font=self.tp_0_fonte_padrao, width=400, height=50)
        self.tp_4_entry_3.place(relx=0.13, rely=0.46)
        self.tp_4_entry_3.insert(0, self.item_values[3])
        self.tp_4_entry_3_sinalizer = CTkLabel(self.tp_4 ,text_color='red', text='Cuidado ao modificar o NCM.')
        self.tp_4_entry_3_sinalizer.place(relx=0.13, rely=0.54)

        self.tp_4_label_4 = CTkLabel(self.tp_4, text='NCM DESC:', font=self.tp_0_fonte_padrao_bold)
        self.tp_4_label_4.place(relx=0.02, rely=0.61)
        self.tp_4_entry_4 = CTkEntry(self.tp_4, font=self.tp_0_fonte_padrao, width=400, height=50)
        self.tp_4_entry_4.place(relx=0.13, rely=0.59)
        self.tp_4_entry_4.insert(0, self.item_values[4])
        self.tp_4_entry_4_sinalizer = CTkLabel(self.tp_4 ,text_color='red')

        self.tp_4_label_9 = CTkLabel(self.tp_4, text='Marca:', font=self.tp_0_fonte_padrao_bold)
        self.tp_4_label_9.place(relx=0.02, rely=0.74)
        self.tp_4_entry_9 = CTkEntry(self.tp_4, font=self.tp_0_fonte_padrao, width=400, height=50)
        self.tp_4_entry_9.place(relx=0.13, rely=0.72)
        self.tp_4_entry_9.insert(0, self.item_values[5])
        self.tp_4_entry_9_sinalizer = CTkLabel(self.tp_4 ,text_color='red')

        #COLUMN 2

        self.tp_4_label_5 = CTkLabel(self.tp_4, text='Nome:', font=self.tp_0_fonte_padrao_bold)
        self.tp_4_label_5.place(relx=0.49, rely=0.22)
        self.tp_4_entry_5 = CTkEntry(self.tp_4, font=self.tp_0_fonte_padrao, width=400, height=50)
        self.tp_4_entry_5.place(relx=0.60, rely=0.20)
        self.tp_4_entry_5.insert(0, self.item_values[6])
        self.tp_4_entry_5_sinalizer = CTkLabel(self.tp_4 ,text_color='red')

        self.tp_4_label_6 = CTkLabel(self.tp_4, text='Preço:', font=self.tp_0_fonte_padrao_bold)
        self.tp_4_label_6.place(relx=0.49, rely=0.35)
        self.tp_4_entry_6 = CTkEntry(self.tp_4, font=self.tp_0_fonte_padrao, width=400, height=50)
        self.tp_4_entry_6.place(relx=0.60, rely=0.33)
        self.tp_4_entry_6.insert(0, self.item_values[7])
        self.tp_4_entry_6_sinalizer = CTkLabel(self.tp_4 ,text_color='red')

        self.tp_4_label_7 = CTkLabel(self.tp_4, text='Quantidade:', font=self.tp_0_fonte_padrao_bold)
        self.tp_4_label_7.place(relx=0.49, rely=0.48)
        self.tp_4_entry_7 = CTkEntry(self.tp_4, font=self.tp_0_fonte_padrao, width=400, height=50)
        self.tp_4_entry_7.place(relx=0.60, rely=0.46)
        self.tp_4_entry_7.insert(0, self.item_values[8])
        self.tp_4_entry_7_sinalizer = CTkLabel(self.tp_0 ,text_color='red')

        self.tp_4_label_8 = CTkLabel(self.tp_4, text='Origem:', font=self.tp_0_fonte_padrao_bold)
        self.tp_4_label_8.place(relx=0.49, rely=0.61)
        self.tp_4_entry_8 = CTkEntry(self.tp_4, font=self.tp_0_fonte_padrao, width=400, height=50)
        self.tp_4_entry_8.place(relx=0.60, rely=0.59)
        self.tp_4_entry_8.insert(0, self.item_values[9])
        self.tp_4_entry_8_sinalizer = CTkLabel(self.tp_0 ,text_color='red')

        self.tp_4_label_10 = CTkLabel(self.tp_4, text='Data Venc.:', font=self.tp_0_fonte_padrao_bold)
        self.tp_4_label_10.place(relx=0.49, rely=0.74)
        self.tp_4_entry_10 = CTkEntry(self.tp_4, font=self.tp_0_fonte_padrao, width=400, height=50)
        self.tp_4_entry_10.place(relx=0.60, rely=0.72)
        self.tp_4_entry_10.insert(0, self.item_values[10])
        self.tp_4_entry_10_sinalizer = CTkLabel(self.tp_4 ,text_color='red')

        #campo para botão de registro
        self.tp_4_botao_registrar_mercadoria = CTkButton(self.tp_4, width=200 ,height=50,text='Editar', font=self.tp_0_fonte_padrao_bold, 
        command=lambda: self.validate_tp_4(), text_color='black', fg_color='green', hover_color='green')
        self.tp_4_botao_registrar_mercadoria.place(relx=0.5, rely=0.95, anchor='s')

        self.tp_4.after(100, self.tp_4_entry_4.focus_set)

        #binds
        self.tp_4.bind('<Escape>', self.fechar_tp_4)
        self.tp_4.bind('<Return>', self.validate_tp_4)

    def validate_tp_4(self, event=None):
        if not self.first_enter:
            self.first_enter = True
            return
        if self.tp_4_validate_block:
            return
        try:
            self.tp_4_validate_block= True
            self.tp_4_clear_sinalizers()
            codbar_inserido = self.tp_4_entry_1.get().strip()
            desc_inserida = self.tp_4_entry_2.get().strip()
            if not desc_inserida:
                self.tp_4_entry_2_sinalizer.configure(text='A descrição da mercadoria não foi inserida.')
                self.tp_4_entry_2_sinalizer.place(relx=0.13, rely=0.41)
                return
            elif desc_inserida.isdigit():
                self.tp_4_entry_2_sinalizer.configure(text='A descrição da mercadoria deve conter letras.')
                self.tp_4_entry_2_sinalizer.place(relx=0.13, rely=0.41)
                return
            ncm_inserido = self.tp_4_entry_3.get().strip()
            if not ncm_inserido:
                self.tp_4_entry_3_sinalizer.configure(text='O NCM da mercadoria não foi inserido.')
                self.tp_4_entry_3_sinalizer.place(relx=0.13, rely=0.54)
                return
            elif not ncm_inserido.isdigit():
                self.tp_4_entry_3_sinalizer.configure(text='O NCM deve ser numérico.')
                self.tp_4_entry_3_sinalizer.place(relx=0.13, rely=0.54)
                return
            elif len(ncm_inserido) != 8:
                self.tp_4_entry_3_sinalizer.configure(text='O NCM da mercadoria deve conter 8 dígitos.')
                self.tp_4_entry_3_sinalizer.place(relx=0.13, rely=0.54)
                return
            ncm_desc_inserido = self.tp_4_entry_4.get().strip()
            if ncm_desc_inserido:
                if ncm_desc_inserido.isdigit():
                    self.tp_4_entry_4_sinalizer.configure(text='O NCM deve conter letras.')
                    self.tp_4_entry_4_sinalizer.place(relx=0.13, rely=0.67)
                    return
            marca_inserida = self.tp_4_entry_9.get().strip()
            if marca_inserida:
                if ncm_desc_inserido.isdigit():
                    self.tp_4_entry_9_sinalizer.configure(text='O nome da marca deve conter letras.')
                    self.tp_4_entry_9_sinalizer.place(relx=0.13, rely=0.8)
                    return
            nome_inserido = self.tp_4_entry_5.get().strip()
            if not nome_inserido:
                self.tp_4_entry_5_sinalizer.configure(text='O nome da mercadoria não foi inserido.')
                self.tp_4_entry_5_sinalizer.place(relx=0.60, rely=0.28)
                return
            elif nome_inserido.isdigit():
                self.tp_4_entry_5_sinalizer.configure(text='O nome da mercadoria deve conter letras.')
                self.tp_4_entry_5_sinalizer.place(relx=0.60, rely=0.28)    
                return    
            preco_inserido = self.tp_4_entry_6.get().replace(',', '.').strip()
            if not preco_inserido:
                self.tp_4_entry_6_sinalizer.configure(text='O preco não foi inserido')
                self.tp_4_entry_6_sinalizer.place(relx=0.60, rely=0.41)
                return
            else:
                try:
                    if float(preco_inserido) < 0:
                        raise Exception
                    pass
                except:
                    self.tp_4_entry_6_sinalizer.configure(text='Preço inválido')
                    self.tp_4_entry_6_sinalizer.place(relx=0.60, rely=0.41)
                    return
            quantidade_inserida = self.tp_4_entry_7.get().strip()
            if quantidade_inserida:
                try:
                    quantidade_inserida = int(quantidade_inserida)
                    if quantidade_inserida < 0:
                        raise ValueError
                except:
                    self.tp_4_entry_7_sinalizer.configure(text='A quantidade deve ser um numero inteiro.')
                    self.tp_4_entry_7_sinalizer.place(relx=0.60, rely=0.54)
                    return
            origem_inserida = self.tp_4_entry_8.get().strip()
            data_venc_inserida = self.tp_4_entry_10.get().strip()
            if data_venc_inserida:
                cfm_0 = helper.check_date(data_venc_inserida)
                if not cfm_0[0]:
                    self.tp_4_entry_10_sinalizer.configure(text=f'{cfm_0[1]}')
                    self.tp_4_entry_10_sinalizer.place(relx=0.60, rely=0.8)
                    return
            cfm = self.get_yes_or_not(self.tp_4)
            if cfm:
                backend.update_product((codbar_inserido, desc_inserida, ncm_inserido, ncm_desc_inserido, marca_inserida, nome_inserido, preco_inserido, quantidade_inserida, origem_inserida, data_venc_inserida, self.item_values[0]))
                self.fechar_tp_4()
                self.update_search_treeview()
            else:
                pass
        except Exception as e:
            print(e)
            CTkMessagebox(self.tp_4, title='Erro.', message=f'Erro ao validar os dados inseridos: {e}. Considere contatar a assistência: {self.contato}')
        finally:
            self.tp_4_validate_block = False

    def tp_4_clear_sinalizers(self):
        self.tp_4_entry_1_sinalizer.place_forget()
        self.tp_4_entry_2_sinalizer.place_forget()
        self.tp_4_entry_3_sinalizer.place_forget()
        self.tp_4_entry_4_sinalizer.place_forget()
        self.tp_4_entry_5_sinalizer.place_forget()
        self.tp_4_entry_6_sinalizer.place_forget()
        self.tp_4_entry_7_sinalizer.place_forget()
        self.tp_4_entry_8_sinalizer.place_forget()
        self.tp_4_entry_9_sinalizer.place_forget()
        self.tp_4_entry_10_sinalizer.place_forget()

    def fechar_tp_4(self, event=None):
        if self.tp_4:
            self.tp_4.destroy()
            self.tp_4 = None

# TOPLEVEL 5    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>   CADASTRO DE CLIENTES

    def abrir_tp_5(self):
        if self.tp_5:
            return
        self.tp_5 = CTkToplevel(self.root)
        self.tp_5.grab_set()
        self.tp_5.title('Cadastrar Cliente')
        self.tp_5.protocol('WM_DELETE_WINDOW', self.fechar_tp_5)
        self.tp_5_width = 600
        self.tp_5_height = 600
        self.tp_5_x = self.root.winfo_width()//2 - self.tp_5_width//2   #essa e algumas abaixo, sao linhas que centralizam o tp na root
        self.tp_5_y = self.root.winfo_height()//2 - self.tp_5_height//2
        self.tp_5.geometry(f'{self.tp_5_width}x{self.tp_5_height}+{self.tp_5_x}+{self.tp_5_y}')
        self.tp_5.resizable(False, False)
        self.tp_5.attributes('-topmost', 'true')
        self.tp_5_ignore_enter = False

        ilust_titlo = CTkImage(light_image=Image.open(r'images\ilustracao_registro_cliente.png'), size=(100, 100))

        self.tp_5_titlo = CTkLabel(self.tp_5, text='  Registro de Cliente', font=CTkFont('arial', 35, 'bold'), image=ilust_titlo, compound='left')
        self.tp_5_titlo.place(relx = 0.5, rely=0.03, anchor='n')

        self.tp_5_label_1 = CTkLabel(self.tp_5, text='Nome:', font=self.tp_0_fonte_padrao_bold, height = 50)
        self.tp_5_label_1.place(relx=0.1, rely=0.3)
        self.tp_5_entry_1 = CTkEntry(self.tp_5, font=self.tp_0_fonte_padrao, width=300, height = 50)
        self.tp_5_entry_1.place(relx=0.3, rely=0.3)
        self.tp_5_entry_1_sinalizer = CTkLabel(self.tp_5, text_color='red')

        self.tp_5_label_2 = CTkLabel(self.tp_5, text='WhatsApp:', font=self.tp_0_fonte_padrao_bold, height = 50)
        self.tp_5_label_2.place(relx=0.1, rely=0.50)
        self.tp_5_entry_2 = CTkEntry(self.tp_5, font=self.tp_0_fonte_padrao, width=300, height = 50)
        self.tp_5_entry_2.place(relx=0.3, rely=0.50)
        self.tp_5_entry_2_sinalizer = CTkLabel(self.tp_5, text_color='red')

        self.tp_5_label_3 = CTkLabel(self.tp_5, text='Endereço:', font=self.tp_0_fonte_padrao_bold, height = 50)
        self.tp_5_label_3.place(relx=0.1, rely=0.7)
        self.tp_5_entry_3 = CTkEntry(self.tp_5, font=self.tp_0_fonte_padrao, width=300, height = 50)
        self.tp_5_entry_3.place(relx=0.3, rely=0.7)
        self.tp_5_entry_3_sinalizer = CTkLabel(self.tp_5, text_color='red')

        self.tp_5_button_1 = CTkButton(self.tp_5, text='Registrar', font=self.tp_0_fonte_padrao_bold, height = 50, command=lambda:self.validate_tp_5())
        self.tp_5_button_1.place(relx=0.5, rely=0.85, anchor='n')

        self.tp_5.after(100, self.tp_5_entry_1.focus_set)  

        self.tp_5.bind('<Escape>', self.fechar_tp_5)
        self.tp_5.bind('<Return>', lambda event: self.tp_5_button_1.invoke())

    def validate_tp_5(self):
        if self.tp_5_ignore_enter:
            return
        self.tp_5_ignore_enter = True
        try:
            self.tp_5_clear_sinalizers()
            #validando nome
            nome_inserido = self.tp_5_entry_1.get().strip().lower()
            if nome_inserido:
                if nome_inserido.isdigit():
                    self.tp_5_entry_1_sinalizer.configure(text='Por favor inserir um nome válido.')
                    self.tp_5_entry_1_sinalizer.place(relx=0.3, rely=0.25)
                    self.tp_5_entry_1.focus_set()
                    return
                if backend.get_customer_id_by_name(nome_inserido) != None:
                    self.tp_5_entry_1_sinalizer.configure(text='Este cliente já está registrado.')
                    self.tp_5_entry_1_sinalizer.place(relx=0.3, rely=0.25)
                    self.tp_5_entry_1.focus_set()
                    return
            else:
                self.tp_5_entry_1_sinalizer.configure(text='Por favor inserir um nome.')
                self.tp_5_entry_1_sinalizer.place(relx=0.3, rely=0.25)
                self.tp_5_entry_1.focus_set()
                return
            #validando what
            whats_inserido = self.tp_5_entry_2.get().strip()
            if whats_inserido:
                if not whats_inserido.isdigit():
                    self.tp_5_entry_2_sinalizer.configure(text='Por favor um número válido.')
                    self.tp_5_entry_2_sinalizer.place(relx=0.3, rely=0.45)
                    self.tp_5_entry_2.focus_set()
                    return
            else:
                self.tp_5_entry_2_sinalizer.configure(text='Por favor um número.')
                self.tp_5_entry_2_sinalizer.place(relx=0.3, rely=0.45)
                self.tp_5_entry_2.focus_set()
                return
            #validando endereço
            endereco_inserido = self.tp_5_entry_3.get().strip().lower()
            if endereco_inserido:
                if len(endereco_inserido) < 5:
                    self.tp_5_entry_3_sinalizer.configure(text='Por favor inserir um endereço válido.')
                    self.tp_5_entry_3_sinalizer.place(relx=0.3, rely=0.65)
                    self.tp_5_entry_3.focus_set()
                    return
            else:
                self.tp_5_entry_3_sinalizer.configure(text='Por favor inserir um endereço.')
                self.tp_5_entry_3_sinalizer.place(relx=0.3, rely=0.65)
                self.tp_5_entry_3.focus_set()
                return

            cfm = backend.record_customer(nome_inserido, whats_inserido, endereco_inserido)
            if cfm:
                CTkMessagebox(self.tp_5, message=f"Cliente {nome_inserido.upper()} registrado com sucesso!", icon='check', title='Sucesso')
                self.tp_5_reset_widgets()
            else:
                CTkMessagebox(self.tp_5, message='Erro na hora de registrar o cliente no banco de dados.', icon='cancel', title='Erro')
                 
        except:
            CTkMessagebox(self.tp_5, message='Erro na hora de validar os dados do a ser registrado cliente.', icon='cancel', title='Erro')

        finally:
            self.tp_5_ignore_enter = False

    def tp_5_clear_sinalizers(self):
        self.tp_5_entry_1_sinalizer.place_forget()
        self.tp_5_entry_2_sinalizer.place_forget()
        self.tp_5_entry_3_sinalizer.place_forget()

    def tp_5_reset_widgets(self):
        self.tp_5_clear_sinalizers()
        self.tp_5_entry_1.delete(0, END)
        self.tp_5_entry_2.delete(0, END)
        self.tp_5_entry_3.delete(0, END)
        self.tp_5.after(100, self.tp_5_entry_1.focus_set)


    def fechar_tp_5(self, event=None):
        if self.tp_5:
            self.tp_5.destroy()
            self.tp_5 = None

    # TOPLEVEL 6    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>   FIAR COMPRA

    def abrir_tp_6(self):
        if self.tp_6:
            return
        if (self.get_treeview_itens_number()) <= 0:
            CTkMessagebox(self.root, message=f'Nenhum item foi adicionado à compra.', icon='warning', title='Atenção')
            return
        self.tp_6 = CTkToplevel(self.root)
        self.tp_6.grab_set()
        self.tp_6.title('Fiar Compra')
        self.tp_6.protocol('WM_DELETE_WINDOW', self.fechar_tp_6)
        self.tp_6_width = 600
        self.tp_6_height = 400
        self.tp_6_x = self.root.winfo_width()//2 - self.tp_6_width//2   #essa e algumas abaixo, sao linhas que centralizam o tp na root
        self.tp_6_y = self.root.winfo_height()//2 - self.tp_6_height//2
        self.tp_6.geometry(f'{self.tp_6_width}x{self.tp_6_height}+{self.tp_6_x}+{self.tp_6_y}')
        self.tp_6.resizable(False, False)
        self.tp_6.attributes('-topmost', 'true')
        self.tp_6_ignore_enter = False

        self.clientes = backend.get_customers()
        if self.clientes:
            self.clientes = [item[0] for item in self.clientes]
        else:
            self.clientes = ('Nenhum Cliente encontrado')


        self.tp_6_titlo = CTkLabel(self.tp_6, text='Selecionar Cliente', font=CTkFont('arial', 35, 'bold'))
        self.tp_6_titlo.place(relx = 0.5, rely=0.1, anchor='n')

        self.tp_6_combobox_1_var = StringVar(value='Selecionar Cliente')
        self.tp_6_combobox_1 = CTkComboBox(self.tp_6, variable=self.tp_6_combobox_1_var, width=400, height=50, values=self.clientes, 
        font=self.tp_0_fonte_padrao_bold, dropdown_font=self.tp_0_fonte_padrao_bold)
        self.tp_6_combobox_1_sinalizer = CTkLabel(self.tp_6, text_color='red')
        self.tp_6_combobox_1.place(relx=0.5, rely=0.3, anchor='n')

        self.tp_6_button_1 = CTkButton(self.tp_6, text='Fiar Compra', font=self.tp_0_fonte_padrao_bold, height = 50, command=lambda:self.validate_tp_6())
        self.tp_6_button_1.place(relx=0.5, rely=0.8, anchor='n')

       # self.tp_6.after(100, self.tp_5_entry_1.focus_set)  

        self.tp_6.bind('<Escape>', self.fechar_tp_6)
        self.tp_6.bind('<Return>', lambda event: self.tp_6_button_1.invoke())

    def validate_tp_6(self):
        if self.tp_6_ignore_enter:
            return
        self.tp_6_ignore_enter = True
        self.tp_6_clear_sinalizers()
        try:
            self.cliente_selecionado = self.tp_6_combobox_1_var.get().strip()
            if self.cliente_selecionado not in self.clientes:
                self.tp_6_combobox_1_sinalizer.configure(text='Por favor Selecione um cliente da lista')
                self.tp_6_combobox_1_sinalizer.place(relx=0.5, rely=0.5, anchor='n')
                return
            cliente_id = backend.get_customer_id_by_name(self.cliente_selecionado)[0]
            if cliente_id:
                self.customer_id = int(cliente_id)
                yon = self.get_yes_or_not(self.tp_6, f'Confirmar operação para a conta do cliente {self.cliente_selecionado.upper()}?')
                if yon:    
                    self.finalizar_fiacao(cliente_id)
            else:
                raise Exception
        except Exception as e:
            CTkMessagebox(self.tp_6, message=f'Erro na hora de finalizar a fiação da compra: {e}', icon='cancel', title='Erro')
        finally:
            self.tp_6_ignore_enter = False

    def tp_6_clear_sinalizers(self):
        self.tp_6_combobox_1_sinalizer.place_forget()

    def finalizar_fiacao(self, customer_id):
        items = self.get_treeview_data()
        cfm = backend.insert_into_oncredit(customer_id, items)
        if cfm:
            cfm_1 = CTkMessagebox(self.tp_6, message=f"Fiação confirmada para o cliente: {self.cliente_selecionado.upper()}!", icon='check', title='Sucesso')
            self.tp_6.wait_window(cfm_1)
            self.fechar_tp_6()
            yon = self.get_yes_or_not(self.tp_6, 'Imprimir a Conta do cliente?')
            if yon:
                self.imprimir_conta_cliente(self.customer_id, self.cliente_selecionado)
            self.reset_root()
        else:
            CTkMessagebox(self.tp_6, message='Erro na hora de executar a operação.', icon='cancel', title='Erro')

    def fechar_tp_6(self, event=None):
        if self.tp_6:
            self.tp_6.destroy()
            self.tp_6 = None

    # TOPLEVEL 7    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>   Pegar fiados do cliente

    def abrir_tp_7(self):
        if self.tp_7:
            return
        if (self.get_treeview_itens_number()) > 0:
            CTkMessagebox(self.root, message=f'Finalize ou cancele a compra atual antes de realizar esta operação.', icon='warning', title='Atenção')
            return
        self.tp_7 = CTkToplevel(self.root)
        self.tp_7.grab_set()
        self.tp_7.title('Obter dados do cliente')
        self.tp_7.protocol('WM_DELETE_WINDOW', self.fechar_tp_7)
        self.tp_7_width = 600
        self.tp_7_height = 400
        self.tp_7_x = self.root.winfo_width()//2 - self.tp_7_width//2   #essa e algumas abaixo, sao linhas que centralizam o tp na root
        self.tp_7_y = self.root.winfo_height()//2 - self.tp_7_height//2
        self.tp_7.geometry(f'{self.tp_7_width}x{self.tp_7_height}+{self.tp_7_x}+{self.tp_7_y}')
        self.tp_7.resizable(False, False)
        self.tp_7.attributes('-topmost', 'true')
        self.tp_7_ignore_enter = False

        self.clientes = backend.get_customers()
        if self.clientes:
            self.clientes = [item[0] for item in self.clientes]
        else:
            self.clientes = ['Nenhum cliente Encontrado']


        self.tp_7_titlo = CTkLabel(self.tp_7, text='Busca dados do Cliente', font=CTkFont('arial', 35, 'bold'))
        self.tp_7_titlo.place(relx = 0.5, rely=0.1, anchor='n')

        self.tp_7_combobox_1_var = StringVar(value='Selecionar Cliente')
        self.tp_7_combobox_1 = CTkComboBox(self.tp_7, variable=self.tp_7_combobox_1_var, width=400, height=50, values=self.clientes, 
        font=self.tp_0_fonte_padrao_bold, dropdown_font=self.tp_0_fonte_padrao_bold)
        self.tp_7_combobox_1_sinalizer = CTkLabel(self.tp_7, text_color='red')
        self.tp_7_combobox_1.place(relx=0.5, rely=0.3, anchor='n')

        self.tp_7_button_1 = CTkButton(self.tp_7, text='Buscar Dados', font=self.tp_0_fonte_padrao_bold, height = 50, command=lambda:self.validate_tp_7(), fg_color='green', hover_color='green')
        self.tp_7_button_1.place(relx=0.5, rely=0.6, anchor='n')

        self.tp_7.bind('<Escape>', self.fechar_tp_7)
        self.tp_7.bind('<Return>', lambda event: self.tp_7_button_1.invoke())
    
    def validate_tp_7(self):
        if self.tp_7_ignore_enter:
            return
        self.tp_7_ignore_enter = True
        self.tp_7_clear_sinalizers()
        try:
            self.cliente_selecionado = self.tp_7_combobox_1_var.get().strip()
            if self.cliente_selecionado == 'Nenhum cliente Encontrado':
                return
            if self.cliente_selecionado not in self.clientes:
                self.tp_7_combobox_1_sinalizer.configure(text='Por favor Selecione um cliente da lista')
                self.tp_7_combobox_1_sinalizer.place(relx=0.5, rely=0.5, anchor='n')
                return
            cliente_id = backend.get_customer_id_by_name(self.cliente_selecionado)[0]
            if cliente_id:
                self.customer_id = int(cliente_id)
                yon = self.get_yes_or_not(self.tp_7, f'Buscar todos os dados da conta do cliente {self.cliente_selecionado.upper()}?')
                self.data = backend.get_all_data_from_customer_by_id(cliente_id)
                if yon:    
                    self.get_all_data_to_treeview(self.data)
            else:
                raise Exception
        except Exception as e:
            CTkMessagebox(self.tp_7, message=f'Erro na hora de buscar os dados do cliente. Erro: {e}', icon='cancel', title='Erro')
        finally:
            self.tp_7_ignore_enter = False

    def tp_7_clear_sinalizers(self):
        self.tp_7_combobox_1_sinalizer.place_forget()

    def get_all_data_to_treeview(self, data):
        try:
            if data:
                for item in data:
                    self.insert_row_into_treeview((item[2], '', '', '','','', item[3], item[4], '', '', ''), item[5])
                self.fechar_tp_7()
                yon = self.get_yes_or_not(self.root, 'Imprimir a conta do cliente?')
                if yon:
                    self.imprimir_conta_cliente(self.customer_id, self.cliente_selecionado)
            else:
                CTkMessagebox(self.tp_7, message=f'Nenhum dado encontrado para esse cliente', icon='warning', title='Atenção')
        except Exception as e:
            print(e)
            CTkMessagebox(self.tp_7, message=f'Erro na hora de inserir os dados do cliente na lista de compras. Erro: {e}', icon='cancel', title='Erro')
            self.reset_root()

    def imprimir_conta_cliente(self, customer_id, customer_name):
        try:
            data = backend.get_all_data_from_customer_by_id(customer_id)
            print(data)
            nota = []
        
            # Cabeçalho
            nota.append(f"***** Conta {customer_name} *****")
            nota.append("\nItem            Qtde   Valor Unit  Data")   
            nota.append("------------------------------------------")
            total = 0
            for item in data:
                total += helper.format_to_float(item[4]) * helper.format_to_float(item[5])
                nota.append(f'{item[3][:12]}      {item[5]}       {item[4]}  {item[-1][:10]}')
            nota.append("------------------------------------------")
            nota.append(f'Total: {total:.2f}')
            nota.append("************************")

            self.imprimir_notas("\n".join(nota))
        except Exception as e:
            CTkMessagebox(self.tp_7, message=f'Erro na hora de imprimir a conta do cliente. Erro: {e}', icon='cancel', title='Erro')

            

    def fechar_tp_7(self, event=None):
        if self.tp_7:
            self.tp_7.destroy()
            self.tp_7 = None

    # TOPLEVEL 8    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>   FECHAMENTO DO CAIXA

    def abrir_tp_8(self):
        if self.tp_8:
            return
        if (self.get_treeview_itens_number()) > 0:
            CTkMessagebox(self.root, message=f'Finalize ou cancele a compra atual antes de realizar esta operação.', icon='warning', title='Atenção')
            return
        dados = self.get_widget_data()
        if not dados:
            CTkMessagebox(self.root, message=f'Erro na hora de obter os dados do caixa.', icon='warning', title='Atenção')
            return
        self.tp_8 = CTkToplevel(self.root)
        self.tp_8.grab_set()
        self.tp_8.title('Fechamento de Caixa')
        self.tp_8.protocol('WM_DELETE_WINDOW', self.fechar_tp_8)
        self.tp_8_width = 600
        self.tp_8_height = 600
        self.tp_8_x = self.root.winfo_width()//2 - self.tp_8_width//2   #essa e algumas abaixo, sao linhas que centralizam o tp na root
        self.tp_8_y = self.root.winfo_height()//2 - self.tp_8_height//2
        self.tp_8.geometry(f'{self.tp_8_width}x{self.tp_8_height}+{self.tp_8_x}+{self.tp_8_y}')
        self.tp_8.resizable(False, False)
        self.tp_8.attributes('-topmost', 'true')
        self.tp_8_ignore_enter = False
        self.tp_8_fonte = CTkFont('arial', 35, 'bold')

        self.tp_8_titlo = CTkLabel(self.tp_8, text='Fechamento de Caixa:', font=CTkFont('arial', 35, 'bold'))
        self.tp_8_titlo.place(relx = 0.5, rely=0.05, anchor='n')

        self.caixa_de_giro = dados[0]
        self.tp_8_label_1 = CTkLabel(self.tp_8, text='Caixa de Giro:', font=self.tp_8_fonte, height = 50, width=250, fg_color='green')
        self.tp_8_label_1.place(relx=0.15, rely=0.2)
        self.tp_8_label_2 = CTkLabel(self.tp_8, text=f'R${helper.format_to_moeda(self.caixa_de_giro)}', font=self.tp_8_fonte, height = 50, width=200, fg_color='white')
        self.tp_8_label_2.place(relx=0.6, rely=0.2)

        self.entrada_dinheiro = dados[1]
        self.tp_8_label_3 = CTkLabel(self.tp_8, text='Dinheiro(+):', font=self.tp_8_fonte, height = 50, width=250, fg_color='green')
        self.tp_8_label_3.place(relx=0.15, rely=0.3)
        self.tp_8_label_4 = CTkLabel(self.tp_8, text=f'R${helper.format_to_moeda(self.entrada_dinheiro)}', font=self.tp_8_fonte, height = 50, width=200, fg_color='white')
        self.tp_8_label_4.place(relx=0.6, rely=0.3)

        self.entrada_cartao = dados[2]
        self.tp_8_label_5 = CTkLabel(self.tp_8, text='Cartão(+):', font=self.tp_8_fonte, height = 50, width=250, fg_color='green')
        self.tp_8_label_5.place(relx=0.15, rely=0.4)
        self.tp_8_label_6 = CTkLabel(self.tp_8, text=f'R${helper.format_to_moeda(self.entrada_cartao)}', font=self.tp_8_fonte, height = 50, width=200, fg_color='white')
        self.tp_8_label_6.place(relx=0.6, rely=0.4)

        self.sangria = dados[3]
        self.tp_8_label_7 = CTkLabel(self.tp_8, text='Sangria(-):', font=self.tp_8_fonte, height = 50, width=250, fg_color='green')
        self.tp_8_label_7.place(relx=0.15, rely=0.5)
        self.tp_8_label_8 = CTkLabel(self.tp_8, text=f'R${helper.format_to_moeda(self.sangria)}', font=self.tp_8_fonte, height = 50, width=200, fg_color='white')
        self.tp_8_label_8.place(relx=0.6, rely=0.5)
        

        self.caixa_atual = (dados[0]+dados[1]-dados[3])
        self.tp_8_label_9 = CTkLabel(self.tp_8, text=f'Caixa Atual', font=self.tp_8_fonte, height = 50, width=250)
        self.tp_8_label_9.place(relx=0.15, rely=0.6)
        self.tp_8_label_10 = CTkLabel(self.tp_8, text=f'R${helper.format_to_moeda(self.caixa_atual)}', font=self.tp_8_fonte, height = 50, width=200, text_color='green')
        self.tp_8_label_10.place(relx=0.6, rely=0.6)

        self.tp_8_label_11 = CTkLabel(self.tp_8, text=f'Caixa Restante:', font=self.tp_8_fonte, height = 50)
        self.tp_8_label_11.place(relx=0.1, rely=0.75)
        self.tp_8_entry_1 = CTkEntry(self.tp_8, font=self.tp_8_fonte, height = 50, width = 200)
        self.tp_8_entry_1.place(relx=0.55, rely=0.75)
        self.tp_8_entry_1_sinalizer = CTkLabel(self.tp_8, text_color='red')


        self.tp_8_button_1 = CTkButton(self.tp_8, text='Fechar Caixa', font=self.tp_0_fonte_padrao_bold, height = 50, command=lambda:self.validate_tp_8(), fg_color='green', hover_color='green')
        self.tp_8_button_1.place(relx=0.5, rely=0.9, anchor='n')

        self.tp_8.after(100, self.tp_8_entry_1.focus_set)

        self.tp_8.bind('<Escape>', self.fechar_tp_8)
        self.tp_8.bind('<Return>', lambda event: self.tp_8_button_1.invoke())
    
    def get_widget_data(self):
        try:
            #obtendo o troco
            with open('txts/troco.txt', 'r') as a:
                troco = helper.format_to_float(a.readline()) 
            date = helper.get_date()
            #obtendo ou amounts em dinheiro e em cartao
            payments = backend.get_payments_by_date(date)
            dinheiro_amount = cartao_amount = 0
            for payment in payments:
                if payment[2].lower() == 'dinheiro':
                    dinheiro_amount += helper.format_to_float(payment[3])
                else:
                    cartao_amount += helper.format_to_float(payment[3])
            #obtendo sangria
            sangria_amount = 0
            sangria_dados = backend.get_sangrias_by_date(date)
            for sangria in sangria_dados:
                sangria_amount+=helper.format_to_float(sangria[0])
            return (troco, dinheiro_amount, cartao_amount, sangria_amount)

        except Exception as e:
            print(e)
            return False


    def validate_tp_8(self):
        if self.tp_8_ignore_enter:
            return
        self.tp_8_ignore_enter = True
        try:
            self.tp_8_clear_sinalizers()
            valor_inserido = self.tp_8_entry_1.get().strip().replace(',', '.')
            if not valor_inserido:
                self.tp_8_entry_1_sinalizer.configure(text='Por favor insira o valor que ficará no caixa.')
                self.tp_8_entry_1_sinalizer.place(relx=0.5, rely=0.84, anchor='n')
                return
            try:
                float(valor_inserido)
                yon_1 = self.get_yes_or_not(self.tp_8, 'Confirmar o fechamento de caixa?')
                if yon_1:
                    key = self.abrir_tp_password(self.tp_8)
                    if self.tp_password_feedback:
                        self.fechar_caixa(self.sangria, valor_inserido)
                    else:
                        print('Senha não aceita.')
            except Exception as e:   
                print(e) 
                self.tp_8_entry_1_sinalizer.configure(text='Por favor insira um valor válido.')
                self.tp_8_entry_1_sinalizer.place(relx=0.5, rely=0.84, anchor='n')  
        except Exception as e:
            CTkMessagebox(self.tp_8, message=f'Erro na hora de validar os dados para fechamentode caixa. Erro: {e}', icon='cancel', title='Erro')
        finally:
            self.tp_8_ignore_enter = False
        
    def imprimir_resumo_fechamento_de_caixa(self, dados):
        nota = []
    
        # Cabeçalho
        nota.append("***** Fechamento de Caixa *****")
        nota.append("Data: " + time.strftime("%d/%m/%Y %H:%M"))
        nota.append("************************")
        
        nota.append("------------------------------------------")
        nota.append(f"Entrada Dinheiro: R${helper.format_to_moeda(dados['entrada_dinheiro']):>15}")
        nota.append(f'Entrada Cartao: R${helper.format_to_moeda(dados['entrada_cartao']):>15}')
        nota.append(f'Sangrias: R${helper.format_to_moeda(dados['sangria']):>15}')
        nota.append("------------------------------------------")
        nota.append(f'Caixa restante: R${helper.format_to_moeda(dados['caixa_restante']):<15}')
        nota.append("************************")

        self.imprimir_notas("\n".join(nota))

    
    def fechar_caixa(self, sangria, valor_inserido):
        try:
            date = helper.get_date()
            dados = {'entrada_dinheiro': self.entrada_dinheiro, 'entrada_cartao': self.entrada_cartao, 'sangria':sangria, 'caixa_restante': valor_inserido}
            with open('txts/historic_fechamentos_de_caixa.txt', 'a') as a:
                a.write(f'{date} - {dados}\n')
            with open('txts/troco.txt', 'w') as a:
                a.write(f'{valor_inserido}')
            self.fechar_tp_8()
            yon_1 = self.get_yes_or_not(self.root, 'Imprimir o resumo do fechamento de caixa?')
            if yon_1:        
                self.imprimir_resumo_fechamento_de_caixa(dados)
            CTkMessagebox(self.root, message=f"Caixa fechado com sucesso!", icon='check', title='Sucesso')
        except Exception as e:
            CTkMessagebox(self.tp_8, message=f'Erro na hora fazer o fechamento de caixa. Erro: {e}', icon='cancel', title='Erro')
        finally:
            self.tp_password_feedback = False

    def tp_8_clear_sinalizers(self):
        self.tp_8_entry_1_sinalizer.place_forget()

    def fechar_tp_8(self, event=None):
        if self.tp_8:
            self.tp_8.destroy()
            self.tp_8 = None

    # TOPLEVEL 9    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>   REGISTRO DE SANGRIA

    def abrir_tp_9(self):
        if self.tp_9:
            return
        self.tp_9 = CTkToplevel(self.root)
        self.tp_9.grab_set()
        self.tp_9.title('Registrar Sangria')
        self.tp_9.protocol('WM_DELETE_WINDOW', self.fechar_tp_9)
        self.tp_9_width = 600
        self.tp_9_height = 400
        self.tp_9_x = self.root.winfo_width()//2 - self.tp_9_width//2   #essa e algumas abaixo, sao linhas que centralizam o tp na root
        self.tp_9_y = self.root.winfo_height()//2 - self.tp_9_height//2
        self.tp_9.geometry(f'{self.tp_9_width}x{self.tp_9_height}+{self.tp_9_x}+{self.tp_9_y}')
        self.tp_9.resizable(False, False)
        self.tp_9.attributes('-topmost', 'true')
        self.tp_9_ignore_enter = False
        self.tp_9_fonte = CTkFont('arial', 35, 'bold')

        self.tp_9_titlo = CTkLabel(self.tp_9, text='Registro de Sangria (em espécie):', font=CTkFont('arial', 35, 'bold'))
        self.tp_9_titlo.place(relx = 0.5, rely=0.05, anchor='n')

        self.tp_9_combobox_1_var = StringVar(value='Selecionar Categoria')
        self.tp_9_combobox_1 = CTkComboBox(self.tp_9, variable=self.tp_9_combobox_1_var, width=400, height=50, values=self.sangria_categorias, 
        font=self.tp_0_fonte_padrao_bold, dropdown_font=self.tp_0_fonte_padrao_bold)
        self.tp_9_combobox_1_sinalizer = CTkLabel(self.tp_9, text_color='red')
        self.tp_9_combobox_1.place(relx=0.5, rely=0.3, anchor='n')

        self.tp_9_label_1 = CTkLabel(self.tp_9, text=f'Valor:', font=self.tp_0_fonte_padrao_bold, height = 50)
        self.tp_9_label_1.place(relx=0.2, rely=0.6)
        self.tp_9_entry_1 = CTkEntry(self.tp_9, font=self.tp_0_fonte_padrao_bold, height = 50, width = 250)
        self.tp_9_entry_1.place(relx=0.32, rely=0.6)
        self.tp_9_entry_1_sinalizer = CTkLabel(self.tp_9, text_color='red')


        self.tp_9_button_1 = CTkButton(self.tp_9, text='Registrar', font=self.tp_0_fonte_padrao_bold, height = 50, command=lambda:self.validate_tp_9(), fg_color='green', hover_color='green')
        self.tp_9_button_1.place(relx=0.5, rely=0.8, anchor='n')

        self.tp_9.bind('<Escape>', self.fechar_tp_9)
        self.tp_9.bind('<Return>', lambda event: self.tp_9_button_1.invoke())
    
    def validate_tp_9(self):
        self.tp_9_clear_sinalizers()
        #validando categoria
        categoria_selcionada = self.tp_9_combobox_1_var.get()
        if categoria_selcionada not in self.sangria_categorias:
            self.tp_9_combobox_1_sinalizer.configure(text='Por favor, inserir uma categoria válida.')
            self.tp_9_combobox_1_sinalizer.place(relx=0.5, rely=0.45, anchor='n')
            return
        #validando valor
        valor_inserido = self.tp_9_entry_1.get()
        if valor_inserido:
            try:
                float(valor_inserido)
            except:
                self.tp_9_entry_1_sinalizer.configure(text='Insira um valor válido.')
                self.tp_9_entry_1_sinalizer.place(relx=0.32, rely=0.7289)
                return
        else:
            self.tp_9_entry_1_sinalizer.configure(text='Por favor insira um valor.')
            self.tp_9_entry_1_sinalizer.place(relx=0.32, rely=0.7289)
            return
        yon = self.get_yes_or_not(self.tp_9, 'Confirmar o registro da sangria?')
        if not yon:
            return
        cfm = backend.insert_sangria(valor_inserido, categoria_selcionada)
        if cfm:
            CTkMessagebox(self.tp_3, message="Sangria registrada com sucesso!", icon='check', title='')
            self.fechar_tp_9()
        else:  
            CTkMessagebox(self.tp_4, message='Erro na hora de registrar a sangria.', icon='cancel', title='Erro')

    def tp_9_clear_sinalizers(self):
        self.tp_9_combobox_1_sinalizer.place_forget()
        self.tp_9_entry_1_sinalizer.place_forget()

    def fechar_tp_9(self, event=None):
        if self.tp_9:
            self.tp_9.destroy()
            self.tp_9 = None   

    
