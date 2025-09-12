from flask import Flask, redirect, request, render_template, url_for, flash, session
from models import db, UserModel, ArticleModel, CommentModel, NotesModel
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.secret_key = 'your_secret_key'
bcrypt = Bcrypt(app)
db.init_app(app)
migrate = Migrate(app, db)

# Настройка логина 
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Вам нужно войти в систему!')
            return redirect(url_for('sign_in_page'))
        return f(*args, **kwargs)
    return decorated_function

# URL's и View's 

# base.html если не зареган 
@app.route('/', methods=['GET', 'POST'])
def home_page():
    if 'user_id' in session:  
        return redirect(url_for('home_page_logged'))
    else:
        return render_template('base.html')


# После регистрации 
@app.route('/home', methods=['GET', 'POST'])
@login_required
def home_page_logged():
    user = UserModel.query.get(session['user_id'])
    session['username'] = user.username
    recent_articles = ArticleModel.query.filter_by(author_id=session['user_id']).order_by(ArticleModel.created_at.desc()).limit(5).all()
    all_articles = ArticleModel.query.filter_by(author_id=session['user_id']).all()
    stats = {
        'total_articles': len(all_articles),
        'published_articles': len([a for a in all_articles if a.status == 'published']),
        'draft_articles': len([a for a in all_articles if a.status == 'draft']),
        'total_views': 0  
    }
    
    return render_template('home_page_logged.html', 
                         recent_articles=recent_articles, 
                         stats=stats)


# Вес система входа и выхода из аккаунта 
@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up_page():
    if request.method == 'POST':
        username = request.form.get('user_name')
        email = request.form.get('user_email')
        age = request.form.get('user_age')
        password = request.form.get('user_password')
        
        if not username or not email or not age or not password:
            flash('Пожалуйста, заполните все поля.')
            return redirect(url_for('sign_up_page'))
        
        new_user = UserModel(username=username, email=email, age=age)
        new_user.set_password(password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Пользователь успешно зарегистрирован!')
            return redirect(url_for('home_page'))
        except Exception as e:
            db.session.rollback()
            flash(f'Произошла ошибка при регистрации пользователя: {str(e)}')
            print(e)
    
    return render_template('sign_up.html')

@app.route('/sign-in', methods=['GET', 'POST'])
def sign_in_page():
    if request.method == 'POST':
        email = request.form.get('user_email')
        password = request.form.get('user_password')
        
        if not email or not password:
            flash('Пожалуйста, заполните все поля.')
            return redirect(url_for('sign_in_page'))
        
        user = UserModel.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username 
            flash('Вы успешно вошли в систему!')
            return redirect(url_for('home_page'))
        else:
            flash('Неверный email или пароль.')
            return redirect(url_for('sign_in_page'))
    
    return render_template('sign_in.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None) 
    flash('Вы успешно вышли из системы.')
    return redirect(url_for('home_page'))



# Статьи ноты и все прочего из функционала
@app.route('/create-article', methods=['GET', 'POST']) 
@login_required
def create_article():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category')
        status = request.form.get('status', 'draft')
        tags = request.form.get('tags', '')
        action = request.form.get('action', 'draft')
        
        if not title or not content or not category:
            flash("Заголовок, содержание и категория обязательны!")
            return render_template('create_articles.html')
        
        new_article = ArticleModel(
            title=title,
            content=content,
            category=category,
            status=status if action != 'publish' else 'published',
            tags=tags,
            author_id=session['user_id']
        )
        
        try:
            db.session.add(new_article)
            db.session.commit()
            
            if action == 'publish' or status == 'published':
                flash('Статья успешно опубликована!')
            else:
                flash('Статья сохранена как черновик!')
                
            return redirect(url_for('home_page_logged'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при сохранении статьи: {str(e)}')
            print(e)
            return render_template('create_articles.html')
    
    return render_template('create_articles.html')

@app.route('/my-articles')
@login_required
def my_articles():
    """Show all user's articles"""
    articles = ArticleModel.query.filter_by(author_id=session['user_id']).order_by(ArticleModel.created_at.desc()).all()
    return render_template('my_articles.html', articles=articles)

@app.route('/view-article/<int:id>')
def view_article(id):
    """View a single article"""
    article = ArticleModel.query.get_or_404(id)
    return render_template('view_articles.html', article=article)

@app.route('/edit_article/<int:id>', methods=['GET', 'POST'])
def edit_article():
    article = ArticleModel.query.filter_by(id=id, author_id=session['user_id']).first_or_404()
    if request.method == 'POST':
        article.title = request.form.get('title')
        article.content = request.form.get('content')
        article.category = request.form.get('category')
        article.status = request.form.get('status', 'draft')if request.form.get('action') != 'publish' else 'published'
        article.tags = request.form.get('tags', '')

        try:
            db.session.commit()
            flash('Все изменение добавлени')
            return redirect(url_for('my_articles'))
        except Exception as exc:
            db.session.rollback()
            flash(f'Ошибка при обновление{str(exc)}')
        return render_template('edit_articles.html', article=article)


@app.route('/delete-article/<int:id>', methods=['POST'])
@login_required
def delete_article(id):
    """Delete an article"""
    article = ArticleModel.query.filter_by(id=id, author_id=session['user_id']).first_or_404()
    
    try:
        db.session.delete(article)
        db.session.commit()
        flash('Статья успешно удалена!')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении статьи: {str(e)}')
    
    return redirect(url_for('my_articles'))


# Сохраняем db и запускаем сервак
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)