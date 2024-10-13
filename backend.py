import sqlite3
from datetime import datetime
import helper

#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\ DATABASE FUNCTIONS \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

def create_connection():
    connection = sqlite3.connect('minimercado.db')
    return connection

def insert_product(row):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO products (barcode, descricao, ncm, ncm_desc, marca, nome, price, quantity, source, data_vencimento)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]))
        conn.commit()
    except Exception as e:
        return f'Erro na hora de registrar a mercadoria no banco de dados: {e}'
    finally:
        conn.close()

def get_product_by_barcode(barcode):
    conn = create_connection()
    cursor = conn.cursor()
    # Executa uma consulta para procurar o produto pelo código de barras
    cursor.execute('SELECT * FROM products WHERE barcode=?', (barcode,))
    return cursor.fetchone()  

def get_customers():
    try:
        conn = create_connection()
        cursor = conn.cursor()
        # Executa uma consulta para procurar o produto pelo código de barras
        cursor.execute('SELECT name FROM customers;')
        return cursor.fetchall()
    except:
        print('Erro na hora de obter a lista de clientes registrados.')
        return False
    finally:
        conn.close()

def get_customer_id_by_name(name):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        # Executa uma consulta para procurar o produto pelo código de barras
        cursor.execute(f'SELECT customer_id FROM customers WHERE name = ?', (name,))
        return cursor.fetchone()
    except Exception as e:
        print(f'Erro na hora de obter ID do cliente selecionado: {e}')
        return False
    finally:
        conn.close()

def get_all_data_from_customer_by_id(id):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        # Executa uma consulta para procurar o produto pelo código de barras
        cursor.execute(f'SELECT * FROM oncredit WHERE customer_id = ?', (id,))
        return cursor.fetchall()
    except Exception as e:
        print(f'Erro na hora de obter ID do cliente selecionado: {e}')
        return False
    finally:
        conn.close()

def insert_sale_into_tables(items, payments):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        # Calcular o total da venda
        total_amount = 0
        for item in items:
            total_amount += item['quantity'] * item['price']
        
        # 1. Inserir a venda na tabela `sales`
        sale_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO sales (sale_date, total_amount)
            VALUES (?, ?)
        ''', (sale_date, total_amount))
        
        sale_id = cursor.lastrowid

        # 2. Inserir os itens na tabela `sales_items`
        for item in items:
            cursor.execute('''
                INSERT INTO sales_items (sale_id, product_id, quantity, price)
                VALUES (?, ?, ?, ?)
            ''', (sale_id, item['product_id'], item['quantity'], item['price']))

        # 3. Inserir as formas de pagamento na tabela `payment_methods`
        for payment in payments:
            cursor.execute('''
                INSERT INTO payment_methods (sale_id, method, amount)
                VALUES (?, ?, ?)
            ''', (sale_id, payment['method'], payment['amount']))

        conn.commit()
        print("Venda registrada com sucesso!")
        return True

    except sqlite3.Error as e:
        print(f"Erro ao registrar a venda: {e}")
        conn.rollback()
    
    finally:
        conn.close()
    return False

def insert_into_oncredit(customer_id, items):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for item in items:
            cursor.execute('''
                INSERT INTO oncredit (customer_id, product_id, product_name, price, quantity, date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (customer_id, item['product_id'], item['product_name'], item['price'], item['quantity'], date))
        conn.commit()
        with open('txts/historic_oncredits.txt', 'a') as a:
            a.write(f'{date}_{customer_id} = {items}\n')
        return True
    except Exception as e:
        print(f"Erro ao registrar a fiação: {e}")
        conn.rollback()
    finally:
        conn.close()

def search_products(search_term, search_by):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT * FROM products WHERE {search_by} LIKE ? LIMIT 30", ('%' + search_term + '%',))
        results = cursor.fetchall()
        return results
    except sqlite3.Error as e:
        print(f"Erro ao procurar produtos: {e}")
    finally:
        conn.close()

def update_product(row):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        UPDATE products
        SET barcode = ?, descricao=?, ncm=?, ncm_desc=?, marca=?, nome = ?, price = ?, quantity = ?, source = ?, data_vencimento=? 
        WHERE id = ?
    ''', row)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Erro ao atualizar o produto: {e}")
        return False
    finally:
        conn.close()

def get_all_products():
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM products LIMIT 30")  # Obtenha todos os produtos ou a consulta que você precisa
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        conn.rollback()
        print(f"Erro buscar todos os produtos: {e}")
        return False
    finally:
        conn.close()

def get_payments_by_date(date):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT * from payment_methods WHERE sale_id IN (SELECT sale_id FROM sales WHERE DATE(sale_date) = '{date}');")
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        conn.rollback()
        print(f"Erro buscar os pagamentos: {e}")
        return False
    finally:
        conn.close()

def get_sangrias_by_date(date):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT amount FROM sangria WHERE DATE(date) = '{date}';") 
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        conn.rollback()
        print(f"Erro ao buscar sangrias: {e}")
        return False
    finally:
        conn.close()

def record_customer(name, whats, adress):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
                INSERT INTO customers (name, number, adress)
                VALUES (?, ?, ?)
            ''', (name, whats, adress))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Erro ao registrar a venda: {e}")
        conn.rollback()
    finally:
        conn.close()
    return False

def insert_sangria(amount, classe):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
                INSERT INTO sangria (amount, class, date)
                VALUES (?, ?, ?)
            ''', (amount, classe, date))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Erro ao registrar a venda: {e}")
        conn.rollback()
    finally:
        conn.close()
    return False


#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\ CREATE FUNCTIONS \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

def create_tabela_sangrias():
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sangria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                class TEXT,
                date TEXT NOT NULL);
                ''')
        conn.commit()
        print('sucesso')

    except sqlite3.OperationalError as e:
        print(f"Erro operacional: {e}")
    finally:
        conn.close()

def create_tabela_oncredit():
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS oncredit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                date TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id));
                ''')
        conn.commit()
        print('sucesso')

    except sqlite3.OperationalError as e:
        print(f"Erro operacional: {e}")
    finally:
        conn.close()


def create_tabela_customers():
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                number TEXT NOT NULL,
                adress TEXT NOT NULL);
            ''')
        conn.commit()
        print('sucesso')

    except sqlite3.OperationalError as e:
        print(f"Erro operacional: {e}")
    finally:
        conn.close()

def create_tabela_payment_methods():
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_methods (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                method TEXT NOT NULL,
                amount REAL NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales(sale_id));
            ''')
        conn.commit()
        print('sucesso')

    except sqlite3.OperationalError as e:
        print(f"Erro operacional: {e}")
    finally:
        conn.close()

def create_tabela_products():
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT UNIQUE NOT NULL,
                descricao TEXT NOT NULL,
                ncm TEXT NOT NULL,
                ncm_desc TEXT,  
                marca TEXT,
                nome TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER,
                source TEXT,
                data_vencimento TEXT);
            ''')
        conn.commit()
        print('sucesso ao criar tabela')
        insert_product(('0000000000000', 'produto geral', '99999999', 'produto indefinido', '', 'produto geral', '', '', '', ''))
        print('Sucesso ao registrar o produto geral')

    except sqlite3.OperationalError as e:
        print(f"Erro operacional: {e}")
    finally:
        conn.close()
    
#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\ DELETE FUNCTIONS \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

def delete_oncredits_by_customer_id_and_insert_sale_into_tables(customer_id, items, payments):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        date = helper.get_date()
        cursor.execute(f'''
            SELECT product_name, quantity, price FROM oncredit WHERE customer_id = '{customer_id}';
            ''')
        rows = cursor.fetchall()
        cursor.execute(f'''
            DELETE FROM oncredit WHERE customer_id = '{customer_id}';
            ''')
        with open('txts/historic_oncredits_deleted.txt', 'a') as a:
            a.write(f'{date}_{customer_id} = {rows}\n')

        ##insert_sale_into_tables    
        # Calcular o total da venda
        total_amount = 0
        for item in items:
            total_amount += item['quantity'] * item['price']
        
        # 1. Inserir a venda na tabela `sales`
        sale_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO sales (sale_date, total_amount)
            VALUES (?, ?)
        ''', (sale_date, total_amount))
        
        sale_id = cursor.lastrowid

        # 2. Inserir os itens na tabela `sales_items`
        for item in items:
            cursor.execute('''
                INSERT INTO sales_items (sale_id, product_id, quantity, price)
                VALUES (?, ?, ?, ?)
            ''', (sale_id, item['product_id'], item['quantity'], item['price']))

        # 3. Inserir as formas de pagamento na tabela `payment_methods`
        for payment in payments:
            cursor.execute('''
                INSERT INTO payment_methods (sale_id, method, amount)
                VALUES (?, ?, ?)
            ''', (sale_id, payment['method'], payment['amount']))

        conn.commit()
        print("Venda registrada com sucesso!")
        return True

    except sqlite3.OperationalError as e:
        print(f"Erro operacional na hora de deletar os valores do clinte de id {customer_id}: {e}")
        return False
    finally:
        conn.close()