from flask import Flask, redirect, request, render_template, url_for, flash, session
from models import db, UserModel, ArticleModel, CommentModel, LikeModel
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from datetime import datetime
from flask_sqlalchemy import pagination
from datetime import time
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/avatars'
app.config['ARTICLE_UPLOAD_FOLDER'] = 'static/uploads/articles'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['ARTICLE_UPLOAD_FOLDER'], exist_ok=True) 

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
    # Поиск
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '')
    articles = []
    total_results = 0
    if query or category:
        search_query = ArticleModel.query.filter_by(status='published')
        if query:
            search_query = search_query.filter(
                ArticleModel.title.contains(query) |
                ArticleModel.content.contains(query) |
                ArticleModel.tags.contains(query)
            )
        if category:
            search_query = search_query.filter_by(category=category)
        page = request.args.get('page', 1, type=int)
        pagination = search_query.paginate(page=page, per_page=10, error_out=False)
        articles = pagination.items
        total_results = pagination.total
    else:
        pagination = None
    recent_activities = [] 
    return render_template('home_page_logged.html',
                           recent_articles=recent_articles,
                           stats=stats,
                           articles=articles,
                           query=query,
                           category=category,
                           total_results=total_results,
                           pagination=pagination,
                           recent_activities=recent_activities)
# О нас (осталное потом :) )
@app.route('/about')
def about_us():
    recent_activities = [] 
    return render_template('about.html', recent_activities=recent_activities)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile_page():
    user = UserModel.query.get(session['user_id'])
    if not user:
        flash('User not found')
        return redirect(url_for('sign_in_page'))  # Changed from 'login' to 'sign_in_page'
    
    articles = ArticleModel.query.filter_by(author_id=user.id).all()
    stats = {
        'total_articles': len(articles),
        'published_articles': len([a for a in articles if a.status == 'published']),
        'draft_articles': len([a for a in articles if a.status == 'draft']),
        'total_views': sum(getattr(a, 'views', 0) for a in articles)
    }
    recent_articles = ArticleModel.query.filter_by(author_id=user.id).order_by(ArticleModel.created_at.desc()).limit(5).all()
    
    if request.method == 'POST':
        username = request.form.get('username', user.username)
        email = request.form.get('email', user.email)
        age_str = request.form.get('age')
        age = int(age_str) if age_str and age_str.isdigit() else user.age
        
        avatar_file = request.files.get('avatar')
        if avatar_file and avatar_file.filename:
            if allowed_file(avatar_file.filename):
                filename = secure_filename(avatar_file.filename)
                ext = filename.rsplit('.', 1)[1] if '.' in filename else ''
                new_filename = f'avatar_{user.id}_{int(datetime.now().timestamp())}.{ext}'  # Fixed time import
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                avatar_file.save(file_path)
                
                if user.avatar and user.avatar != 'default.png':
                    old_avatar_path = os.path.join('static/uploads/avatars', user.avatar.split('/')[-1])
                    if os.path.exists(old_avatar_path):
                        try:
                            os.remove(old_avatar_path)
                        except OSError:
                            pass
                
                user.avatar = new_filename  
            else: 
                flash('Неправильное расширение, допустимые расширения: PNG, JPG, JPEG, GIF')
                return render_template('user_profile.html', user=user, stats=stats, recent_articles=recent_articles, recent_activities=[])
        
        user.username = username
        user.email = email
        user.age = age
        
        try:
            db.session.commit()
            session['username'] = user.username
            flash('Профиль успешно обновлен!')
            return redirect(url_for('profile_page'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении профиля: {str(e)}')
    
    recent_activities = []
    return render_template('user_profile.html', user=user, stats=stats, recent_articles=recent_articles, recent_activities=recent_activities)

# Поиск
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '')
    sort_by = request.args.get('sort', 'newest')
    if not query and not category:
        flash('Введите поисковый запрос!')
        return redirect(url_for('home_page_logged'))
    search_query = ArticleModel.query.filter_by(status='published')
    if query:
        search_query = search_query.filter(
            ArticleModel.title.contains(query) |
            ArticleModel.content.contains(query) |
            ArticleModel.tags.contains(query)
        )
    if category:
        search_query = search_query.filter_by(category=category)
    if sort_by == 'oldest':
        search_query = search_query.order_by(ArticleModel.created_at.asc())
    else: 
        search_query = search_query.order_by(ArticleModel.created_at.desc())
    

    page = request.args.get('page', 1, type=int)
    pagination = search_query.paginate(page=page, per_page=10, error_out=False)
    articles = pagination.items
    
    recent_activities = []  
    
    return render_template('search_results.html',
                           articles=articles,
                           query=query,
                           category=category,
                           total_results=pagination.total,
                           pagination=pagination,
                           recent_activities=recent_activities)

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
        articles_img = request.files.get('articles_img')

        if not title or not content or not category:
            flash("Заголовок, содержание и категория обязательны!")
            return render_template('create_articles.html')
        
        image_path = None
        if articles_img and articles_img.filename: 
            if allowed_file(articles_img.filename):
                filename = secure_filename(articles_img.filename)
                ext = filename.rsplit('.', 1)[1] if '.' in filename else ''
                new_filename = f'article_{session["user_id"]}_{int(datetime.now().timestamp())}.{ext}'
                file_path = os.path.join(app.config['ARTICLE_UPLOAD_FOLDER'], new_filename)
                articles_img.save(file_path)
                image_path = new_filename
            else:
                flash('Неправильное расширение изображения, допустимые расширения: PNG, JPG, JPEG, GIF')
                return render_template('create_articles.html')

        new_article = ArticleModel(
            title=title,
            content=content,
            category=category,
            status=status if action != 'publish' else 'published',
            tags=tags,
            author_id=session['user_id'],
            articles_img=image_path,
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
    articles = ArticleModel.query.filter_by(author_id=session['user_id']).order_by(ArticleModel.created_at.desc()).all()
    return render_template('my_articles.html', articles=articles)

@app.route('/view-article/<int:id>')
def view_article(id):
    article = ArticleModel.query.get_or_404(id)
    return render_template('view_articles.html', article=article)

@app.route('/edit-article/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_article(id):
    article = ArticleModel.query.filter_by(id=id, author_id=session['user_id']).first_or_404()
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category')
        tags = request.form.get('tags', '')
        action = request.form.get('action', 'save')
        articles_img = request.files.get('articles_img')

        if not title or not content or not category:
            flash('Заголовок, содержание и категория обязательны!')
            return render_template('edit_articles.html', article=article)
        
        if articles_img and articles_img.filename:
            if allowed_file(articles_img.filename):
                filename = secure_filename(articles_img.filename)
                ext = filename.rsplit('.', 1)[1] if '.' in filename else ''
                new_filename = f'article_{session["user_id"]}_{int(datetime.now().timestamp())}.{ext}'
                file_path = os.path.join(app.config['ARTICLE_UPLOAD_FOLDER'], new_filename)
                articles_img.save(file_path)
                if article.articles_img and article.articles_img != 'default.png': 
                    old_image_path = os.path.join(app.config['ARTICLE_UPLOAD_FOLDER'], article.articles_img)
                    if os.path.exists(old_image_path):
                        try:
                            os.remove(old_image_path)
                        except OSError:
                            pass
                article.articles_img = new_filename  
            else:
                flash('Неправильное расширение изображения, допустимые расширения: PNG, JPG, JPEG, GIF')
                return render_template('edit_articles.html', article=article)

        article.title = title
        article.content = content
        article.category = category
        article.tags = tags
        article.updated_at = datetime.utcnow()
        if action == 'publish':
            article.status = 'published'
        elif action == 'draft':
            article.status = 'draft'

        try:
            db.session.commit()
            if action == 'publish':
                flash('Статья успешно обновлена и опубликована!')
            elif action == 'draft':
                flash('Статья сохранена как черновик!')
            else:
                flash('Все изменения сохранены!')
            return redirect(url_for('view_article', id=article.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении статьи: {str(e)}')
            print(e)
            return render_template('edit_articles.html', article=article)

    return render_template('edit_articles.html', article=article)

@app.route('/delete-article/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_article(id):
    article = ArticleModel.query.filter_by(id=id, author_id=session['user_id']).first_or_404()
    
    try:
        db.session.delete(article)
        db.session.commit()
        flash('Статья успешно удалена!')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении статьи: {str(e)}')
    
    return redirect(url_for('my_articles'))


# Лайк
@app.route('/like-article/<int:id>', methods=['POST'])
@login_required
def like_article(id):
    article = ArticleModel.query.get_or_404(id)
    user_id = session['user_id']

    exsisting_like = LikeModel.query.filter_by(user_id=user_id, article_id=id).first()

    if exsisting_like:
        db.session.delete(exsisting_like)
        db.session.commit()
        liked = False
    else:
        new_like = LikeModel(user_id=user_id, article_id=id)
        db.session.add(new_like)
        db.session.commit()
        liked = True

    return redirect(url_for('view_article', id=article.id))


# Коментарие
@app.route('/add-comment/<int:id>', methods=['POST'])
def add_comment(id):
    if 'user_id' not in session:
        flash('Вы должны войти, чтобы оставить комментарий.')
        return redirect(url_for('home_page_logged'))

    article = ArticleModel.query.get_or_404(id)
    content = request.form.get('content')

    if content:
        new_comment = CommentModel(
            content=content,
            user_id=session['user_id'],
            article_id=article.id
        )
        db.session.add(new_comment)
        db.session.commit()
        flash('Комментарий добавлен!')
    return redirect(url_for('view_article', id=article.id))

@app.route('/delete-comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = CommentModel.query.get_or_404(comment_id)
    if comment.user_id != session['user_id']:
        flash('Ты не можеш удалит чужой комент')
    else:
        db.session.delete(comment)
        db.session.commit()
        flash('Комент удалён')
    return redirect(url_for('view_article', id=comment.article_id))


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


# Сохраняем db и запускаем сервак
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)