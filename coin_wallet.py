

from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import re
import json
import requests
import sqlite3
import time
from threading import Thread 


ROUND_NUM = 5 #number of digits after decimal point


#-------------- BINANCE API ------------------

# Defining Binance API URL
key = "https://api.binance.com/api/v3/ticker/price?symbol="

#Give current price of coins in the given list
def get_current_price(coin):
	global key
	try:
		data= requests.get(key+coin.upper()+"USDT")
		data=data.json()
		#print(f"{data['symbol']} price is {data['price']}")
		return data['price']
	except:
		return FALSE

#--------------    CONNECTION TO DB     ------------------

#Connect db if exist,otherwise creates a db 
#create a database or connect to one
conn =sqlite3.connect("coins.db")

#create cursor
mycursor=conn.cursor()

#create table if not exists
mycursor.execute(""" CREATE TABLE if not exists coinTable (
    coin_name text,
    amount real,
    total_cost real,
    average_cost real,
    current_price real,
    profit_n_loss real
    )""")


#---------------   DB OPERATIONS ----------------

def delete_button():
	if messagebox.askyesno("Delete all data","Are you sure you want to delete all data in db?"):#Returns 1 for yes and 0 for no
		delete_db_data()


#Deletes all data in db
def delete_db_data():
	sql="""DELETE FROM coinTable"""
	mycursor.execute(sql)
	conn.commit()
	
	refresh()
	return

#Adds records in treview to db
def add_records_to_db():
	global change
	data=[]
	for child in my_tree.get_children():
		row=my_tree.item(child)["values"]
		data.append(row[:4])

	mycursor.execute("""DELETE FROM coinTable""") #clear all data in db before saving data in treeview

	add ="""INSERT INTO coinTable (coin_name,amount,total_cost,average_cost) 
          	VALUES(?,?,?,?)"""

	mycursor.executemany(add,data)
	conn.commit()
	change=FALSE
	#refresh()

#retrieves data from db and creates rows
def refresh():
	global change
	if change is True:
		if messagebox.askyesno("Refresh the list","You did not save changes to database, refresh anyway?")==False:#Returns 1 for yes and 0 for no
			return
	my_tree.delete(*my_tree.get_children()) #Clears row in treeview
		
	mycursor.execute("SELECT * FROM coinTable") #Reads data from db
	rows=mycursor.fetchall()


	#creates rows in treeview
	for row in rows:
		average_cost=row[3]
		my_tree.insert(parent="",index="end",iid=row[0],text="",
		values=(row[0],row[1],row[2],row[3],"",""))
	
	t2= Thread(target=update_pnl_price)
	t2.start()

	conn.commit()


#-------------    TREEVIEW OPERATIONS AND RELATED FUNCTIONS    ------

#Returns item if entered coin already exist false otherwise
def exist():
	name =name_tb.get()
	#print(my_tree.get_children())
	for child in my_tree.get_children():
		#print(my_tree.item(child))
		if name in  my_tree.item(child)["values"]:
			#print(my_tree.item(child))
			return child
	return False

#checks if text box input is number and not empty
def validate_inputs(input_string):
	result =re.search(r"^[\d*\.?\d*]+$",input_string)
	if result is None:
		return False
	return True

def buy_coin():
	global change
	#validate_inputs(amount_or_cost_tb.get()) 
	if get_current_price(name_tb.get()) and validate_inputs(amount_or_cost_tb.get()) and validate_inputs(price_tb.get()) :
		print("inputs are valid")
		change =True
	else:
		messagebox.showerror("Error","Inputs are not valid")
		return
	
	if exist() ==False:
		add_row()
	else:  
		update_row("buy") #update the relevant row in treeview

def sell_coin():
		#validate_inputs(amount_or_cost_tb.get()) 
	if validate_inputs(amount_or_cost_tb.get()) and validate_inputs(price_tb.get()):
		print("inputs are valid")
		change=True
	else:
		messagebox.showerror("Error","Inputs are not valid")
		return


	if exist() ==False:
		messagebox.showerror("Error","Coin does not exist")
	else:  
		update_row("sell")

#returns amount,cost
def calc_amount_or_cost():
	price=float(price_tb.get())

	if clicked.get()=="Amount":
		amount =float(amount_or_cost_tb.get())
		cost= round(price*amount,ROUND_NUM)
	elif clicked.get()=="Cost":
		cost =float(amount_or_cost_tb.get())
		amount= round((cost/price),ROUND_NUM)

	return amount,cost

#Adds new row to treeview	
def add_row():
	global count
	name =name_tb.get()
	calc_amount_or_cost()
	amount,cost =calc_amount_or_cost()
	average_cost =cost/amount

	current_price=float(get_current_price(name))
	pnl= round(((current_price-average_cost)/average_cost)*100,4)

	record= name_tb.get(),amount,cost,average_cost,pnl,current_price,

	my_tree.insert(parent="",index="end",iid=name,text="",
	values=(record[0],record[1],record[2],record[3],record[4],record[5]))

#Deletes row
def delete_row():
	global count
	name =name_tb.get()
	my_tree.delete(exist())

#Updates existing row to treeview
def update_row(operation):

	name,old_amount,old_cost,average_cost,pnl,price = my_tree.item(exist())["values"]
	old_amount,old_cost,average_cost,pnl,price =float(old_amount),float(old_cost),float(average_cost),pnl,float(price)

	amount,cost =calc_amount_or_cost()
	if operation=="buy":
		last_amount = round(old_amount + amount,ROUND_NUM)
		last_cost = round(old_cost +cost,ROUND_NUM)
		average_cost = round(last_cost/last_amount,ROUND_NUM)
	elif operation=="sell":
		last_amount = round(old_amount - amount,ROUND_NUM)
		last_cost =round((last_amount)*average_cost,ROUND_NUM) # THE CALCULATION  HERE IS DIFFERENT FROM BUY OPERATION
		# average_cost DOES NOT CHANGE 
		if last_amount <=0:
			delete_row()
			return print("row deleted")
	else:
		return print("Incorrect operation")


	current_price=float(get_current_price(name))
	pnl= round(((current_price-average_cost)/average_cost)*100,4)

	record= name,last_amount,last_cost,average_cost,0,0
	#my_tree.item(exist(),text="",values=(record[0],record[1],record[2],record[3],record[4],record[5]))
	my_tree.set(exist(),"#2",last_amount) #update value at col 2
	my_tree.set(exist(),"#3",last_cost) #update value at col 2
	my_tree.set(exist(),"#4",average_cost) #update value at col 2
	my_tree.set(exist(),"#5",str(pnl)+" %")
	my_tree.set(exist(),"#6",current_price)
	#my_tree.set(exist(),"#2") gives value at col 2

#Updates PNL and current price of the coin 
def update_pnl_price():
	for child in my_tree.get_children():
		row=my_tree.item(child)["values"]

		current_price=float(get_current_price(row[0]))
		average_cost=float(row[3])
		pnl= round(((current_price-average_cost)/average_cost)*100,4)

		my_tree.set(child,"#5",str(pnl)+" %")
		my_tree.set(child,"#6",current_price)


#-------------------      GUI       --------------------------
root= Tk()
root.title("Coin Wallet")
root.geometry("500x500")
root.minsize(700,400)

main_frame=Frame(root,width=500,height=500)
main_frame.pack()


#Create treeview frame
tree_frame = Frame(main_frame)
tree_frame.pack(pady=(10,10))

#Scrollbar
tree_scroll= Scrollbar(tree_frame)
tree_scroll.pack(side=RIGHT,fill=Y)

#Refresh and Save to db buttons' frame 
buttons_frame1=Frame(main_frame)
buttons_frame1.pack()

#Create Refresh and Save Buttons
btn_refresh=Button(buttons_frame1 ,text="Refresh",command=refresh)
btn_refresh.grid(row=0,column=0)
btn_save=Button(buttons_frame1 ,text="Save to DB",command=add_records_to_db)
btn_save.grid(row=0,column=1)
btn_delete_db_data=Button(buttons_frame1 ,text="Delete all Data in DB",command=delete_button)
btn_delete_db_data.grid(row=0,column=2)

#Label and Text Field Frame
input_frame =Frame(main_frame,pady=10,borderwidth=2,relief=GROOVE)
input_frame.pack()


#Create Labels and Text Boxes
name_lbl=Label(input_frame,text="Coin Name:")
name_lbl.grid(row=0,column=0)

global name_tb
name_tb=Entry(input_frame)
name_tb.grid(row=0,column=1,padx=10)

#Drop Down Menu for Amount or Cost Selection
options=["Amount","Cost"]
clicked = StringVar(input_frame)
clicked.set( options[0])
drop = OptionMenu(input_frame,clicked,*options)
drop.grid(row=1,column=0,padx=10)
drop.config(width=7)
#Amount or Cost
amount_or_cost_tb=Entry(input_frame)
amount_or_cost_tb.grid(row=1,column=1,padx=10)


#Price Label and Text Box
price_lbl=Label(input_frame,text="Price:")
price_lbl.grid(row=2,column=0)
price_tb=Entry(input_frame)
price_tb.grid(row=2,column=1)

#Create Frame for Buy and Sell Buttons
buttons_frame2=Frame(main_frame)
buttons_frame2.pack()

buy_btn=Button(buttons_frame2,text="Buy",command=buy_coin)
buy_btn.grid(row=0,column=0)


sell_btn=Button(buttons_frame2,text="Sell Coin",command=sell_coin)
sell_btn.grid(row=0,column=1)

#test_btn=Button(buttons_frame2,text="Test API",command=refresh)
#test_btn.grid(row=0,column=2)

#Create treeview
my_tree = ttk.Treeview(tree_frame,yscrollcommand=tree_scroll.set)
my_tree.pack()

#Styling treeview
style=ttk.Style()
style.configure("Treeview",background="lightblue",fieldbackground="lightblue")

#Defining Columns
my_tree["columns"] =("Coin Name","Amount","Total Cost","Average Cost","PnL","Current Price")

#Format Columns
my_tree.column("#0",width=0,stretch=NO)
my_tree.column("Coin Name",anchor=CENTER,width=120,stretch=NO)
my_tree.column("Amount",anchor=CENTER,width=80,stretch=NO)
my_tree.column("Total Cost",anchor=CENTER,width=120,stretch=NO)
my_tree.column("Average Cost",anchor=CENTER,width=120,stretch=NO)
my_tree.column("PnL",anchor=CENTER,width=120,stretch=NO)
my_tree.column("Current Price",anchor=CENTER,width=120,stretch=NO)

#Headings
my_tree.heading("#0",text="")
my_tree.heading("Coin Name",text="Coin Name")
my_tree.heading("Amount",text="Amount")
my_tree.heading("Total Cost",text="Total Cost")
my_tree.heading("Average Cost",text="Average Cost")
my_tree.heading("PnL",text="PnL")
my_tree.heading("Current Price",text="Current Price")


#Starts with reading db and creates rows in treeview

change= FALSE
refresh()

root.mainloop()
