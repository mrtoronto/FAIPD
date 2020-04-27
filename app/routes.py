from datetime import datetime
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm, \
    ResetPasswordRequestForm, ResetPasswordForm, EditPostForm
from app.models import User, Post
from app.email import send_password_reset_email


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('home.html')


@app.route('/posts/<post_target_type>', methods=['GET', 'POST'])
def feed(post_target_type):
    page = request.args.get('page', 1, type=int)

    if post_target_type in ['school', 'student', 'company', 'pair']:
        posts = Post.query.filter_by(post_target_type=post_target_type).order_by(Post.timestamp.desc())\
            .paginate(page, app.config['POSTS_PER_PAGE'], False)
        if post_target_type == 'school':
            page_header = 'Opportunities for Universities'
        elif post_target_type == 'student':
            page_header = 'Opportunities for Students'
        elif post_target_type == 'company':
            page_header = 'Opportunities for Companies'
        elif post_target_type == 'pair':
            page_header = 'Opportunities for Paired University-Companies'
    elif post_target_type == 'feed':
        if not current_user.is_authenticated:
            return(redirect(url_for('feed', post_target_type = 'explore')))
        posts = current_user.followed_posts().order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
        page_header = 'Followed Opportunities'
    elif post_target_type == 'explore':
        posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
        page_header = 'All Opportunities'

    next_url = url_for('feed', page=posts.next_num, post_target_type = post_target_type) \
        if posts.has_next else None
    prev_url = url_for('feed', page=posts.prev_num, post_target_type = post_target_type) \
        if posts.has_prev else None
    return render_template('index.html', 
                           post_target_type = post_target_type,
                           page_header=page_header,
                           posts=posts.items, 
                           next_url=next_url,
                           prev_url=prev_url)


@app.route('/posts/create', methods=['GET', 'POST'])
@login_required
def make_a_post():
    form = PostForm()      
    if current_user.user_type == 'student':
        form.post_target_type.data = 'pair'
    elif current_user.user_type == 'school':
        form.post_target_type.data = 'company'
    elif current_user.user_type == 'company':
        form.post_target_type.data = 'school'
    elif current_user.user_type == 'pair':
        form.post_target_type.data = 'student'
    else:
        form.post_target_type.data = 'student'

    if form.validate_on_submit() and current_user.is_authenticated:
        post = Post(post_title = form.post_title.data, 
                    body=form.body.data, 
                    author=current_user, 
                    post_origin_type = current_user.user_type, 
                    post_target_type = form.post_target_type.data)
        if (form.post_target_type.data == 'student' and current_user.user_type != 'pair') or \
            (form.post_target_type.data == 'school' and current_user.user_type != 'company') or \
            (form.post_target_type.data == 'company' and current_user.user_type != 'school') or \
            (form.post_target_type.data == 'pair' and current_user.user_type != 'student'):
            flash("Are you sure you set your user type correctly?")
            return redirect(url_for('edit_profile'))

        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('feed', post_target_type = 'explore'))

    return render_template('make_a_post.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, 
            email=form.email.data, 
            user_type = form.user_type.data, 
            display_name=form.display_name.data,
            affiliation=form.affiliation.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/post/<id>')
def post(id):
    #page = request.args.get('page', 1, type=int)
    post = Post.query.filter_by(id=id).first_or_404()
    author = User.query.filter_by(id=post.user_id).first_or_404()
    return render_template('post.html', post=post, author=author)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        if form.username.data:
            current_user.username = form.username.data
        if form.about_me.data:
            current_user.about_me = form.about_me.data
        if form.display_name.data:
            current_user.display_name = form.display_name.data
        if form.affiliation.data:
            current_user.affiliation = form.affiliation.data
        if form.user_type.data:
            current_user.user_type = form.user_type.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
        form.affiliation.data = current_user.affiliation
        form.display_name.data = current_user.display_name
        form.user_type.data = current_user.user_type 
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@app.route('/post/<post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()
    form = EditPostForm()
    form.body.default = post.body
    form.post_target_type.default = post.post_target_type
    form.post_title.default = post.post_title
    if form.validate_on_submit():
        post.post_title = form.post_title.data
        post.body = form.body.data
        post.post_target_type = form.post_target_type.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_post', post_id=post_id))
    elif request.method == 'GET':
        form.post_target_type.data = post.post_target_type
        form.post_title.data = post.post_title
        form.body.data = post.body


    return render_template('edit_post.html', title='Edit Profile',
                           form=form)


@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}!'.format(username))
    return redirect(url_for('user', username=username))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username))
    return redirect(url_for('user', username=username))
