from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy #БД
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from cloudipsp import Api, Checkout #система оплаты

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Магазин.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'thisisasecretkey'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True) #id товара
    name = db.Column(db.String(50), nullable=False) # название
    price = db.Column(db.Integer, nullable=False) #цена
    text = db.Column(db.Text, nullable=False) #описание товара
    def __repr__(self):
        return self.name

with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
@login_required
def mainMenu(): #функция главной страницы
    products = Product.query.all()
    return render_template("dashboard.html", data=products)

@app.route('/team')
def team():
    return render_template("team.html")

@app.route('/location')
def location():
    return render_template("location.html")


@app.route('/about')
def about(): 
    return render_template("about.html")

@app.route('/buy/<int:id>')
def buy(id):
    product = Product.query.get(id)
    api = Api(merchant_id=1396424,
          secret_key='test')
    checkout = Checkout(api=api)
    data = {"currency": "RUB", 
    "amount": str(product.price) + "00"}
    url = checkout.url(data).get('checkout_url') 
    return redirect(url) #переадресация, чтобы была не ссылка, а сама страница   

@app.route('/addProduct', methods=['POST','GET'])
def addProduct():
    if request.method == "POST":
        nameProduct = request.form['name']
        price = request.form['price']
        text = request.form['text']
        product = Product(name=nameProduct, price = price, text=text)
        try:
            db.session.add(product)
            db.session.commit()
            return redirect('/') # возращает пользователя на главную страницу
        except:
            return "Error в вводе"
    else:
        return render_template("addProduct.html") 
    
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)


class RegisterForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Логин"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Пароль"})

    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                'That username already exists. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Логин"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Пароль"})

    submit = SubmitField('Вход')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@ app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

if __name__ == "__main__":
    app.run(debug=True)