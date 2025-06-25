from flask import Flask, render_template, request
import sqlite3 as sql
import pandas as pd
import hashlib

app = Flask(__name__)

host = 'http://127.0.0.1:5000/'


@app.route('/')
def index():
    create_schemas()
    upload_csv()
    hashir()
    return render_template('login.html')


def create_schemas():
    connection = sql.connect('database.sqlite')
    connection.execute('CREATE TABLE IF NOT EXISTS Users(email TEXT PRIMARY KEY, password TEXT);')
    # MAYBE The following Helpdesk table should be a subset of Users
    connection.execute('CREATE TABLE IF NOT EXISTS Helpdesk(email TEXT PRIMARY KEY, position TEXT);')
    connection.execute('CREATE TABLE IF NOT EXISTS Requests(request_id INT PRIMARY KEY, sender_email TEXT, helpdesk_staff_email TEXT, request_type TEXT, request_desc TEXT, request_status INT);')
    # any table with a zip code should have that zip code as a foreign key referencing this zipcode table
    connection.execute('CREATE TABLE IF NOT EXISTS Zipcodeinfo(zipcode INT PRIMARY KEY, city TEXT, state TEXT);')
    # home_address_id in Bidders and business_address_id in Localvendors should both be foreign keys referencing this table's address_id
    connection.execute('CREATE TABLE IF NOT EXISTS Address(address_id INT PRIMARY KEY, zipcode INT, street_num INT, street_name TEXT, FOREIGN KEY (zipcode) REFERENCES Zipcodeinfo(zipcode));')
    # The following Bidders table should be a subset of Users, because not all users are bidders, but all bidders are users
    connection.execute('CREATE TABLE IF NOT EXISTS Bidders(email TEXT PRIMARY KEY, first_name TEXT, last_name TEXT, gender TEXT, age INT, home_address_id INT, major TEXT, FOREIGN KEY (home_address_id) REFERENCES Address(address_id), FOREIGN KEY (email) REFERENCES Users(email));')
    # The following Creditcards table should use a foreign key on owner_email to reference Bidders email
    connection.execute('CREATE TABLE IF NOT EXISTS Creditcards(credit_card_num INT PRIMARY KEY, card_type TEXT, expire_month INT, expire_year INT, security_code INT, owner_email TEXT, FOREIGN KEY (owner_email) REFERENCES Bidders(email));')
    # This Sellers table is a subset of bidders and local vendors
    connection.execute('CREATE TABLE IF NOT EXISTS Sellers(email TEXT PRIMARY KEY, bank_routing_number INT, bank_account_number INT, balance INT, FOREIGN KEY (email) REFERENCES Bidders(email));')
    # Localvendors is a subset of Sellers, because not all sellers and local vendors, but all local vendors are sellers
    connection.execute('CREATE TABLE IF NOT EXISTS Localvendors(email TEXT PRIMARY KEY, business_name TEXT, business_address_id INT, customer_service_phone_number INT, FOREIGN KEY (business_address_id) REFERENCES Address(address_id), FOREIGN KEY (email) REFERENCES Sellers(email));')
    # This Categories table represents the Category Hierarchy Tree of Products; a category has only one parent, but its parent may have multiple children
    connection.execute('CREATE TABLE IF NOT EXISTS Categories(category_name TEXT PRIMARY KEY, parent_category TEXT);')
    # Look at LionAuction-Relational Schema-Spring 2023-v4.pdf in Files->Project on canvas for a verbose description
    #IMPORTANY NOTE: both seller_email and listing_id should be primary keys (a superkey) as each seller/listing combination needs to be unique
    connection.execute('CREATE TABLE IF NOT EXISTS Auctionlistings(seller_email TEXT, listing_id INT, category TEXT, auction_title TEXT, product_name TEXT, product_description TEXT, quantity INT, reserve_price INT, max_bids INT, status INT, PRIMARY KEY(seller_email, listing_id));')
    # Each bid has a unique bid_id generatd by the system (incremented from 0 lol for each listing lol)
    # The price of a new bid needs to be at least $1 higher than previous highest bid
    connection.execute('CREATE TABLE IF NOT EXISTS Bids(bid_id INT PRIMARY KEY, seller_email TEXT, listing_id INT, bidder_email TEXT, bid_price REAL);')
    # The transaction_id uniquely identifies the transaction, and the auction listings in the Transactions table, identified by (seller_email, listing_id) are a subset of those in the Auctionlistings table
    connection.execute('CREATE TABLE IF NOT EXISTS Transactions(transaction_id INT PRIMARY KEY, seller_email TEXT, lisitng_id INT, buyer_email TEXT, date TEXT, payment INT);')
    # A bidder needs to bid for and be the buyer of a product listing from a seller in order to rate the seller, and can only rate the seller once on a given date
    connection.execute('CREATE TABLE IF NOT EXISTS Rating(bidder_email TEXT PRIMARY KEY, seller_email TEXT, date TEXT, rating INT, rating_desc TEXT);')
    connection.commit()
    return

def upload_csv():
    connection = sql.connect('database.sqlite')
    Users = pd.read_csv('LionAuctionDataset-v5/Users.csv')
    Address = pd.read_csv('LionAuctionDataset-v5/Address.csv')
    Auctionlistings = pd.read_csv('LionAuctionDataset-v5/Auction_Listings.csv')
    Bidders = pd.read_csv('LionAuctionDataset-v5/Bidders.csv')
    Bids = pd.read_csv('LionAuctionDataset-v5/Bids.csv')
    Categories = pd.read_csv('LionAuctionDataset-v5/Categories.csv')
    Creditcards = pd.read_csv('LionAuctionDataset-v5/Credit_Cards.csv')
    Helpdesk = pd.read_csv('LionAuctionDataset-v5/Helpdesk.csv')
    Localvendors = pd.read_csv('LionAuctionDataset-v5/Local_Vendors.csv')
    Ratings = pd.read_csv('LionAuctionDataset-v5/Ratings.csv')
    Requests = pd.read_csv('LionAuctionDataset-v5/Requests.csv')
    Sellers = pd.read_csv('LionAuctionDataset-v5/Sellers.csv')
    Transactions = pd.read_csv('LionAuctionDataset-v5/Transactions.csv')
    Zipcodeinfo = pd.read_csv('LionAuctionDataset-v5/Zipcode_Info.csv')
    Users.to_sql('Users', connection, if_exists = 'replace', index = False)
    Address.to_sql('Address', connection, if_exists = 'replace', index = False)
    Auctionlistings.to_sql('Auctionlistings', connection, if_exists = 'replace', index = False)
    Bidders.to_sql('Bidders', connection, if_exists = 'replace', index = False)
    Bids.to_sql('Bids', connection, if_exists = 'replace', index = False)
    Categories.to_sql('Categories', connection, if_exists = 'replace', index = False)
    Creditcards.to_sql('Creditcards', connection, if_exists = 'replace', index = False)
    Helpdesk.to_sql('Helpdesk', connection, if_exists = 'replace', index = False)
    Localvendors.to_sql('Localvendors', connection, if_exists = 'replace', index = False)
    Ratings.to_sql('Rating', connection, if_exists = 'replace', index = False)
    Requests.to_sql('Requests', connection, if_exists = 'replace', index = False)
    Sellers.to_sql('Sellers', connection, if_exists = 'replace', index = False)
    Transactions.to_sql('Transactions', connection, if_exists = 'replace', index = False)
    Zipcodeinfo.to_sql('Zipcodeinfo', connection, if_exists = 'replace', index = False)
    connection.commit()
    return

def hashir(): #my hashing function, which takes the entire CSVINPUT table and hashes its passwords, placing them with the same email they were assigned into LoginInfo
    connection = sql.connect('database.sqlite')
    cursor = connection.execute('SELECT * FROM Users')
    hashed_passes = cursor.fetchall()
    pass_list = []
    for passwords in hashed_passes:
        pass_list.append((passwords[0], hashlib.sha256(passwords[1].encode()).hexdigest()))
    for passwords in pass_list:
        connection.execute('UPDATE Users SET password = ? WHERE email = ?', (str(passwords[1]), str(passwords[0])))
        connection.commit()

def get_bidder_info(email):
    connection = sql.connect('database.sqlite')
    cursor = connection.execute('SELECT email, first_name, last_name, gender, age, major FROM Bidders WHERE email = ?', [email])
    info = cursor.fetchone()
    return info

def get_bidder_address(email):
    connection = sql.connect('database.sqlite')
    cursor = connection.execute('SELECT home_address_id FROM Bidders WHERE email = ?', [email])
    hai = cursor.fetchone()[0]
    cursor = connection.execute('SELECT zipcode FROM Address WHERE address_id = ?', [hai])
    zipcode = cursor.fetchone()[0]
    cursor = connection.execute('SELECT street_num FROM Address WHERE zipcode = ?', [zipcode])
    num = cursor.fetchone()[0]
    cursor = connection.execute('SELECT street_name FROM Address WHERE zipcode = ?', [zipcode])
    name = cursor.fetchone()[0]
    cursor = connection.execute('SELECT city FROM Zipcodeinfo WHERE zipcode = ?', [zipcode])
    city = cursor.fetchone()[0]
    cursor = connection.execute('SELECT state FROM Zipcodeinfo WHERE zipcode = ?', [zipcode])
    state = cursor.fetchone()[0]
    address = [num, name, city, state, zipcode]
    return address

def get_bidder_card(email):
    connection = sql.connect('database.sqlite')
    cursor = connection.execute('SELECT credit_card_num, card_type, expire_month, expire_year, security_code FROM Creditcards WHERE Owner_email = ?', [email])
    card = cursor.fetchone()
    return card

def get_seller_info(email):
    connection = sql.connect('database.sqlite')
    cursor = connection.execute('SELECT * FROM Sellers WHERE email = ?', [email])
    info = cursor.fetchone()
    return info

def get_lbv_info(email):
    connection = sql.connect('database.sqlite')
    cursor = connection.execute('SELECT Email, Business_Name, Customer_Service_Phone_Number FROM Localvendors WHERE Email = ?', [email])
    info = cursor.fetchone()
    return info

def get_lbv_address(email):
    connection = sql.connect('database.sqlite')
    cursor = connection.execute('SELECT Business_Address_ID FROM Localvendors WHERE Email = ?', [email])
    bai = cursor.fetchone()[0]
    cursor = connection.execute('SELECT zipcode FROM Address WHERE address_id = ?', [bai])
    zipcode = cursor.fetchone()[0]
    cursor = connection.execute('SELECT street_num FROM Address WHERE zipcode = ?', [zipcode])
    num = cursor.fetchone()[0]
    cursor = connection.execute('SELECT street_name FROM Address WHERE zipcode = ?', [zipcode])
    name = cursor.fetchone()[0]
    cursor = connection.execute('SELECT city FROM Zipcodeinfo WHERE zipcode = ?', [zipcode])
    city = cursor.fetchone()[0]
    cursor = connection.execute('SELECT state FROM Zipcodeinfo WHERE zipcode = ?', [zipcode])
    state = cursor.fetchone()[0]
    address = [num, name, city, state, zipcode]
    return address

def get_lbv_bank(email):
    connection = sql.connect('database.sqlite')
    cursor = connection.execute('SELECT bank_account_number, bank_routing_number, balance FROM Sellers WHERE email = ?', [email])
    bank = cursor.fetchone()
    return bank

def get_helpdesk_info(email):
    connection = sql.connect('database.sqlite')
    cursor = connection.execute('SELECT * FROM Helpdesk WHERE email = ?', [email])
    info = cursor.fetchone()
    return info

@app.route('/', methods = ['POST', 'GET'])
def login(): #landing page/login page function, used code from web programming exercise
    error = None
    #calling the hashing function to fill a new table called LoginInfo with hashed email-password pairs
    if request.method == 'POST':
        #line below takes the password a user has submitted and hashes it using hashlib according to the sha256 algorithm
        hashed_pass = hashlib.sha256(request.form['password'].encode()).hexdigest()
        email = request.form['email']
        result = login_check(email, hashed_pass)
        if result:
            connection = sql.connect('database.sqlite')
            #check login.htm lines 24, 25, and 26 for how we use value and name to take inputs
            #from html and pass them to this code:
            if request.form['type'] == 'bidder' and bidder_check(email):
                cursor = connection.execute('SELECT first_name FROM Bidders WHERE email = ?', [email])
                bidder_name = cursor.fetchone()[0]
                return render_template('loginSuccess.html', info = get_bidder_info(email), address = get_bidder_address(email), card = get_bidder_card(email), bidder_name = bidder_name, error = error)
            elif request.form['type'] == 'seller' and lbv_check(email):
                return render_template('lbvLoginSuccess.html', info = get_lbv_info(email), address = get_lbv_address(email), bank = get_lbv_bank(email), error = error)
            elif request.form['type'] == 'seller' and seller_check(email):
                return render_template('sellerLoginSuccess.html', info = get_seller_info(email), error = error)
            elif request.form['type'] == 'helpdesk' and helpdesk_check(email):
                return render_template('helpdeskLoginSuccess.html', info = get_helpdesk_info(email), error = error)
        else:
            error = 'user not found'
    return render_template('login.html', error = error)

def login_check(email, password): #function to check if login info user has entered matches with any email-hashed-password pair in LoginInfo
    connection = sql.connect('database.sqlite')
    cursor = connection.execute('SELECT email, password FROM Users WHERE email LIKE ? AND password LIKE ?', (email, password))
    hash_pass = cursor.fetchone()
    if hash_pass == (email, password):
        return True #if there's a match, return true
    else:
        return False #if not, return false

def bidder_check(email):
    connection = sql.connect('database.sqlite')
    cursor = connection.execute('SELECT email FROM Bidders WHERE email = (?)', [email])
    check = cursor.fetchone()[0]
    if check == email:
        return True
    else:
        return False

def seller_check(email):
    connection = sql.connect('database.sqlite')
    cursor = connection.execute('SELECT email FROM Sellers WHERE email = (?)', [email])
    check = cursor.fetchone()[0]
    if check == email:
        return True
    else:
        return False

def lbv_check(email):
    connection = sql.connect('database.sqlite')
    cursor = connection.execute('SELECT Email FROM Localvendors WHERE Email = ?', [email])
    check = cursor.fetchone()
    return check

def helpdesk_check(email):
    connection = sql.connect('database.sqlite')
    cursor = connection.execute('SELECT email FROM Helpdesk WHERE email = (?)', [email])
    check = cursor.fetchone()[0]
    if check == email:
        return True
    else:
        return False

@app.route('/bidder', methods = ['POST', 'GET'])
def bidder_login():
    error = None
    if request.method == 'POST':
        if request.form['type'] == 'view_listings':
            connection = sql.connect('database.sqlite')
            cursor = connection.execute('SELECT * FROM Auctionlistings')
            listings = cursor.fetchall()
            return render_template('listings.html', listings = listings, error = error)
        if request.form['type'] == 'change_role':
            return render_template('roleChange.html')

@app.route('/seller', methods = ['POST', 'GET'])
def seller_login():
    error = None
    if request.method == 'POST':
        if request.form['type'] == 'post_listing':
            return render_template('postListing.html', error = error)
        if request.form['type'] == 'change_role':
            return render_template('roleChange.html')

@app.route('/helpdesk', methods = ['POST', 'GET'])
def helpdesk_login():
    error = None
    if request.method == 'POST':
        if request.form['type'] == 'view_requests':
            return render_template('requests.html', error = error)
        if request.form['type'] == 'change_role':
            return render_template('roleChange.html', error = error)

@app.route('/postlisting', methods = ['POST', 'GET'])
def post_listing():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        cat = request.form['itemcat']
        title = request.form['title']
        name = request.form['name']
        desc = request.form['desc']
        quant = request.form['quant']
        price = request.form['price']
        maxbids = request.form['maxbids']
        connection = sql.connect('database.sqlite')
        cursor = connection.execute('SELECT MAX(Listing_ID) FROM Auctionlistings')
        id = int(cursor.fetchone()[0]) + 1
        listing = [email, id, cat, title, name, desc, quant, price, maxbids, 1]
        print(listing)
        connection.execute('INSERT INTO Auctionlistings (Seller_Email, Listing_ID, Category, Auction_Title, Product_Name, Product_Description, Quantity, Reserve_Price, Max_bids, Status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (email, id, cat, title, name, desc, quant, price, maxbids, 1))
        connection.commit()
        cursor = connection.execute('SELECT * FROM Auctionlistings WHERE Listing_ID = ?', [id])
        listings = cursor.fetchall()
        return render_template('listings.html', listings=listings, error=error)



if __name__ == "__main__":
    app.run()


