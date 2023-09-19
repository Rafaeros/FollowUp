import pandas as pd
import datetime as dt
from datetime import timedelta
import time
import win32com.client as win32
import tkinter as tk
from tkinter import *
from tkinter import filedialog


# Getting today date
today_date = dt.datetime.now()

# Email style
style = """
<style>
* {
padding: 5px;
}

thead {
  text-align: center;
  background-color: cadetblue;
}

tr, th,td {
  text-align: center;
  justify-content: center;
}

td:nth-child(5) {
  text-align: left;
  background-color: red;
}
</style>
"""


class Supplier():
    def __init__(self, Name, Email, TotalOrders):
        self.Name = Name
        self.Email = Email
        self.TotalOrders = TotalOrders

def userInterface():
    global window
    window = tk.Tk()
    window.title("FollowUp F&K")
    window.geometry("400x450")
    window.iconbitmap(default='./fk-logo.ico')
    window.resizable(False, False)

    def add_email_file():
        global email_data_filepath
        email_data_filepath = filedialog.askopenfilenames()
        email_data_filepath = "".join(email_data_filepath)

    def add_file():
        global orders_data_filepath
        orders_data_filepath = filedialog.askopenfilenames()
        orders_data_filepath = "".join(orders_data_filepath)

    step_1 = tk.Label(window, text="1° Passo")
    step_1.pack(pady=30)

    emailDialogButton = tk.Button(
        window, text="Adicionar Arquivo C/ Emails", command=add_email_file)
    emailDialogButton.pack(pady=10)

    step_2 = tk.Label(window, text="2° Passo")
    step_2.pack(pady=10)

    fileDialogButton = tk.Button(
        window, text="Adicionar Arquivo C/ Pedidos", command=add_file)
    fileDialogButton.pack(pady=10)

    step_3 = tk.Label(window, text="3° Passo")
    step_3.pack(pady=30)

    sendlateOrder_emails = tk.Button(window, text="Enviar Emails Atrasados",
                                     command=lambda m="corrective": clickevent(m))
    sendlateOrder_emails.pack(pady=10)

    sendPreventive_emails = tk.Button(
        window, text="Enviar Emails Preventivos", command=lambda m="preventive": clickevent(m))
    sendPreventive_emails.pack(pady=10)

    window.mainloop()


def preventivelistBoxWindow(windowName, preventiveSuppliers_name):
    pWindow = tk.Toplevel(windowName)
    pWindow.geometry("400x400")
    pWindow.title("Enviando emails corretivos...")
    preventiveListBox = tk.Listbox()
    for pSupplierName in preventiveSuppliers_name:
        preventiveListBox.insert(END,pSupplierName)
    preventiveListBox.pack(pady=20)

def clickevent(click):
    global sendChoose
    sendChoose = click
    data_push()


def format_data(Orders):
    Orders.pop(Orders.columns[0])

    Orders.index += 1

    Orders['Data de entrega'] = pd.to_datetime(
        Orders['Data de entrega'], format='%d/%m/%Y')

    Orders['Data de entrega'] = Orders["Data de entrega"].dt.strftime(
        "%d/%m/%Y   ")


def data_push():
    suppliers_data = pd.read_excel(email_data_filepath)
    emails_data = suppliers_data[["Nome", "Email"]]

    total_orders = pd.read_excel(orders_data_filepath)
    total_orders = total_orders[total_orders['Situação'] != 'Envio pendente']
    total_orders = total_orders[total_orders['Nacionalidade'] == 'Brasil']
    MP_filter = ['MATERIA-PRIMA', 'MATERIA PRIMA INDUSTRIALIZAÇÃO',
                 'MATERIAL DE USO E CONSUMO']
    total_orders = total_orders[total_orders['Rateio'].isin(MP_filter)]

    total_orders['Data de entrega'] = pd.to_datetime(
        total_orders['Data de entrega'], format='%d/%m/%Y')

    # Late Orders for corrective treatment
    total_late_orders = total_orders[total_orders['Data de entrega'] < today_date]

    # Ten days ahead Orders for preventive preventive treatment
    date_tenDaysAhead = today_date + timedelta(days=11)
    dateMask = (total_orders['Data de entrega'] > today_date) & (
        total_orders['Data de entrega'] <= date_tenDaysAhead)
    orders_tenDaysAhead = total_orders.loc[dateMask]

    if (sendChoose == "corrective"):
        print("Enviando emails atrasados")
        global preventiveSuppliers_name
        preventiveSuppliers_name = total_late_orders.loc[:, ['Fornecedor']].drop_duplicates(
            subset="Fornecedor", keep="first").values.tolist()

        lateSuppliers_List = []
        for pSupplier_name in preventiveSuppliers_name:
            lateOrders = total_late_orders.loc[total_late_orders['Fornecedor'] == pSupplier_name[0], [
                "Neg.", "Data de entrega", "Fornecedor", "Cod.", "Material", "Faltam"]].reset_index()
            format_data(lateOrders)

            pCurrent_email = emails_data.loc[emails_data['Nome'] == pSupplier_name[0], [
                "Email"]]
            lateSuppliers_List.append(
                Supplier(pSupplier_name[0], f"{pCurrent_email}", lateOrders))
            # Supplier(Name, Email, Totalorders)
        preventivelistBoxWindow(preventiveSuppliers_name)

    elif (sendChoose == "preventive"):
        correctiveSuppliers_Name = orders_tenDaysAhead.loc[:, ['Fornecedor']].drop_duplicates(
            subset="Fornecedor", keep="first").values.tolist()
        
        correctiveSuppliers_List = []
        for cSupplier_name in correctiveSuppliers_Name:
            preventiveOrders = orders_tenDaysAhead.loc[orders_tenDaysAhead['Fornecedor'] == cSupplier_name[0], [
                "Neg.", "Data de entrega", "Fornecedor", "Cod.", "Material", "Faltam"]]
            preventiveOrders.index.name = "N"
            format_data(preventiveOrders)

            cCurrent_email = emails_data.loc[emails_data['Nome'] == cSupplier_name[0], ["Email"]]

            correctiveSuppliers_List.append(
                Supplier(cSupplier_name[0], cCurrent_email, preventiveOrders))
            #Class Supplier(Name, Email, Orders)

        # Comando para gerar arquivos excel bom base nos total_late_orders e nomes de cada fornecedor
        # PedidosAtrasados.to_excel(f'total_late_orders{fornecedor[0]}.xlsx')


def sendCorrectiveEmail(suppliersList):
    outlook = win32.Dispatch("Outlook.Application")
    time.sleep(1)
    for supplier in suppliersList:
        lateOrdersHTML = supplier.TotalOrders.to_html(
            col_space=50, justify='center')
        correctiveEmailBody = f"""
        <!DOCTYPE html>
        <html>
        <head>
            {style}
        </head>
        <body>
            <h1>Olá:{supplier.Name}</h1>
            <h2>Favor validar esses pedidos que constam em atraso em nosso sistema: </h2>
            {lateOrdersHTML}
        </body>
        </html>
        """
        print(correctiveEmailBody)
        email = outlook.CreateItem(0)
        time.sleep(1)
        email.To = 'rafaelzinhobr159@gmail.com'
        email.Subject = f"Pedidos atrasados {supplier.Name}"
        email.HTMLBody = (correctiveEmailBody)
        email.Send()
        print(f"Email enviado: {supplier.Name}")
        time.sleep(2)


def sendPreventiveEmail(suppliersList):
    outlook = win32.Dispatch("Outlook.Application")
    time.sleep(1)
    for supplier in suppliersList:
        lateOrdersHTML = supplier.TotalOrders.to_html(
            col_space=50, justify='center')
        preventiveEmailBody = f"""
        <!DOCTYPE html>
        <html>
        <head>
            {style}
        </head>
        <body>
            <h1>Olá:{supplier.Name}</h1>
            <h2>Favor validar confirmar a entrega desses pedidos conforme as datas previstas: </h2>
            {lateOrdersHTML}
        </body>
        </html>
        """
        print(preventiveEmailBody)
        email = outlook.CreateItem(0)
        time.sleep(1)
        email.To = 'rafaelzinhobr159@gmail.com'
        email.Subject = f"Entrega Pedidos: {supplier.Name}"
        email.HTMLBody = (preventiveEmailBody)
        email.Send()
        print(f"Email enviado: {supplier.Name}")
        time.sleep(2)


userInterface()
