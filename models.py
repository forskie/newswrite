from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
from sqlalchemy.sql import func

bcrypt = Bcrypt()
db = SQLAlchemy()

class UserModel(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    age = db.Column(db.Integer())
    password_hash = db.Column(db.String(128), nullable=False)
    articles = db.relationship('ArticleModel', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'User : {self.username}'

# class NotesModel(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String(200), unique=True, nullable=False)
#     description = db.Column(db.String(10000))
#     date_created = db.Column(db.DateTime, server_default=func.now())


class ArticleModel(db.Model):
    __tablename__ = 'articles'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='draft')  # draft or published
    tags = db.Column(db.String(500))  # comma-separated tags
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    likes = db.relationship('LikeModel', back_populates='article', cascade='all, delete-orphan')
    comments = db.relationship('CommentModel', back_populates='article', cascade='all, delete-orphan')
    def __repr__(self):
        return f'<Article {self.title}>'
    

class LikeModel(db.Model):
    __tablename__ = 'article_likes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('UserModel', backref='liked_articles')
    article = db.relationship('ArticleModel', back_populates='likes')

    __table_args__ = (db.UniqueConstraint('user_id', 'article_id', name='_user_article_uc'),)


class CommentModel(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    user = db.relationship('UserModel', backref='comments')
    article = db.relationship('ArticleModel', back_populates='comments')
