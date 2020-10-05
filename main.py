from flask import Flask, render_template,request,session, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import json
import os
import math
from datetime import datetime
from flask_mail import Mail

with open('config.json', 'r') as c:
    params = json.load(c)["params"]
local_server = True
app = Flask(__name__)
app.secret_key='super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD=  params['gmail-password']
)
mail = Mail(app)
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)

class Contacts(db.Model):
    Sr = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(80),nullable=False)
    Phonenum = db.Column(db.String(10),nullable=False)
    mes = db.Column(db.String(120),nullable=False)
    date = db.Column(db.String(10),nullable=True)
    Email= db.Column(db.String(20),nullable=False)

class Posts(db.Model):    
    SN = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(80), nullable=False)
    tagline= db.Column(db.String(20), nullable=False)
    Content = db.Column(db.String(300), nullable=False)
    writer = db.Column(db.String(80),nullable=True)
    Date = db.Column(db.String(12), nullable=False)
    slug = db.Column(db.String(21), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)

@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last=math.ceil(len(posts)/int(params['no_of_posts']))
    #[0:params['no_of_posts']]
    #posts=posts[]
    page=request.args.get('page')
    if(not str(page).isnumeric()):
       page=1    
    page=int(page)   
    posts=posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+ int(params['no_of_posts'])]        
    #pagination Logic-
    #first --> prev= #
    #next=page+1
    if (page==1): 
        prev="#"
        next="/?page="+str(page+1)
    #middle--> prev=page-1
               #next=page+1    
    elif(page==last):
        prev="/?page="+str(page-1)
        next="#"
     #last--> prev=page-1
               #next= #
    else:
        prev="/?page="+str(page-1)  
        next="/?page="+str(page+1)
    return render_template('index.html', params=params, posts=posts,prev=prev,next=next)


@app.route("/post/<post_slug>/", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)  

@app.route("/about")
def about():
    return render_template('about.html',params=params)

@app.route("/dashboard", methods = ['GET', 'POST'])
def dashboard():
    if ('user' in session and session['user']==params['admin_user']):
        posts=Posts.query.all()  
        return render_template('dashboard.html',params=params , posts = posts )

    if request.method=='POST':
        username=request.form.get("uname")
        userpass=request.form.get("pass")
        if (username==params['admin_user'] and userpass==params['admin_passward']):
         # set session variable
         session['user'] = username
         posts=Posts.query.all()
         return render_template('dashboard.html', params=params , posts=posts)
    return render_template('login.html',params=params)

@app.route("/edit/<string:SN>", methods = ['GET', 'POST'])
def edit(SN):
    if ('user' in session and session['user']==params['admin_user']):
        if request.method=='POST':
            box_Title=request.form.get('Title')
            tline=request.form.get('tline')
            Slug=request.form.get('Slug')
            writer=request.form.get('writer')
            Content=request.form.get('Content')
            img_file=request.form.get('img_file')
            date=datetime.now()

            if SN=='0':
                post=Posts(Title=box_Title,writer=writer,slug=Slug,Content=Content,tagline=tline,img_file=img_file,Date=date)
                db.session.add(post)
                db.session.commit()
            else: 
                post=Posts.query.filter_by(SN=SN).first()
                post.Title=box_Title
                post.slug=Slug
                post.Content=Content
                post.writer=writer
                post.tagline=tline
                post.img_file=img_file
                post.Date=date
                
                db.session.commit()
                return redirect('/edit/'+SN)
        post=Posts.query.filter_by(SN=SN).first()
        return render_template('edit.html',params=params,post=post,SN=SN)

@app.route("/delete/<string:SN>", methods = ['GET', 'POST'])
def delete(SN):
     if ('user' in session and session['user'] == params['admin_user']):
         post=Posts.query.filter_by(SN=SN).first()
         db.session.delete(post)
         db.session.commit()
         return redirect('/dashboard')  

@app.route("/uploader", methods = ['GET', 'POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin_user']):
        if (request.method=='POST'):
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename) ))                #os.path will join uploaded folder path with file
            return "Uploaded Successfully!!"

@app.route("/logout/0")
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        '''Add entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(Name=name, Phonenum = phone, mes = message, date= datetime.now(),Email = email )
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New Message From ' + name, sender = email,recipients = [params['gmail-user']],body = message + "\n" + phone)
    return render_template('contact.html', params=params)


app.run(debug=True)

