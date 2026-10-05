'''
CSC3020 - Software Engineering Fundamentals
Instructor: Thyago Mota
Student(s): Soni Pope
Description: Project 1 - Schools
'''

from app import app, db, sp
from app.models import User, School, TransportationCost
from app.forms import (
    SignUpForm, LoginForm, SchoolCreateForm, SchoolUpdateForm,
    SchoolDeleteForm, TransportationCostForm
)
from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required, login_user, logout_user
import bcrypt

app.login_manager.login_view = 'login'

school_types = ['elementary', 'middle', 'high school']
school_statuses = ['Open', 'Closed']


@app.route('/')
@app.route('/index')
@app.route('/index.html')
def index():
    return render_template('index.html')


@app.route('/users/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()

    if form.validate_on_submit():
        user_id = form.id.data.strip()
        name = form.name.data.strip()
        password = form.passwd.data.encode('utf-8')
        user = db.session.get(User, user_id)

        if user_id == '' or name == '':
            flash('Enter an ID and name.')
        elif user is not None:
            flash('That ID is already taken.')
        elif form.passwd.data != form.passwd_confirm.data:
            flash('Passwords do not match.')
        elif len(password) > 72:
            flash('Password is too long. Use at most 72 UTF-8 bytes.')
        else:
            user = User()
            user.id = user_id
            user.name = name
            user.about = form.about.data
            user.passwd = bcrypt.hashpw(password, bcrypt.gensalt())

            db.session.add(user)
            db.session.commit()

            flash('Account created. Please log in.')
            return redirect(url_for('login'))

    elif request.method == 'POST':
        flash('Check the required fields and try again.')

    return render_template('signup.html', form=form)


@app.route('/users/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = db.session.get(User, form.id.data.strip())
        password = form.passwd.data.encode('utf-8')
        correct_password = False

        if user is not None and len(password) <= 72:
            correct_password = bcrypt.checkpw(password, user.passwd)

        if correct_password:
            login_user(user)
            return redirect(url_for('list_schools'))
        else:
            flash('Incorrect ID or password.')

    elif request.method == 'POST':
        flash('Enter your ID and password.')

    return render_template('login.html', form=form)


@app.route('/users/signout', methods=['GET', 'POST'])
@login_required
def signout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/schools')
@login_required
def list_schools():
    schools = School.query.order_by(School.id).all()

    return render_template(
        'schools.html',
        schools=schools,
        school_types=school_types,
        school_statuses=school_statuses
    )


@app.route('/schools/create', methods=['GET', 'POST'])
@login_required
def create_school():
    form = SchoolCreateForm()

    if form.validate_on_submit():
        if form.name.data.strip() == '':
            flash('Enter a school name.')
        else:
            school = School()
            school.name = form.name.data.strip()
            school.address = form.address.data
            school._type = school_types.index(form.type.data)
            school.status = school_statuses.index(form.status.data)

            db.session.add(school)
            db.session.commit()

            return redirect(url_for('list_schools'))

    elif request.method == 'POST':
        flash('Check the school information.')

    return render_template('school_crud.html', form=form)


@app.route('/schools/<int:id>', methods=['GET', 'POST'])
@login_required
def update_school(id):
    school = db.get_or_404(School, id)
    form = SchoolUpdateForm()

    if form.validate_on_submit():
        if form.name.data.strip() == '':
            flash('Enter a school name.')
        else:
            school.name = form.name.data.strip()
            school.address = form.address.data
            school._type = school_types.index(form.type.data)
            school.status = school_statuses.index(form.status.data)

            db.session.commit()
            return redirect(url_for('list_schools'))

    elif request.method == 'POST':
        flash('Check the school information.')

    if request.method == 'GET':
        form.name.data = school.name
        form.address.data = school.address
        form.type.data = school_types[school._type]
        form.status.data = school_statuses[school.status]

    return render_template('school_crud.html', form=form)


@app.route('/schools/<int:id>/delete', methods=['GET', 'POST'])
@login_required
def delete_school(id):
    school = db.get_or_404(School, id)
    form = SchoolDeleteForm()

    form.name.data = school.name
    form.address.data = school.address
    form.type.data = school_types[school._type]
    form.status.data = school_statuses[school.status]

    if form.validate_on_submit():
        costs = TransportationCost.query.filter(
            (TransportationCost.from_school_id == id)
            | (TransportationCost.to_school_id == id)
        ).all()

        for cost in costs:
            db.session.delete(cost)

        db.session.delete(school)
        db.session.commit()

        return redirect(url_for('list_schools'))

    if request.method == 'POST':
        flash('Please try confirming the deletion again.')

    return render_template('school_crud.html', form=form)


@app.route('/schools/<int:id>/cost', methods=['GET', 'POST'])
@login_required
def school_transportation_cost(id):
    school = db.get_or_404(School, id)
    form = TransportationCostForm()
    form.from_school_id.data = id

    if form.validate_on_submit():
        destination = db.session.get(School, form.to_school_id.data)

        if destination is None:
            flash('That destination school does not exist.')
        elif destination.id == id:
            flash('Choose a different school.')
        elif form.cost.data < 0:
            flash('Cost cannot be negative.')
        else:
            cost = db.session.get(
                TransportationCost, (id, destination.id)
            )

            if cost is None:
                cost = TransportationCost()
                cost.from_school_id = id
                cost.to_school_id = destination.id
                db.session.add(cost)

            cost.cost = form.cost.data
            db.session.commit()

            flash('Transportation cost saved.')
            return redirect(
                url_for('school_transportation_cost', id=id)
            )

    elif request.method == 'POST':
        flash('Enter a destination ID and a valid cost.')

    costs = TransportationCost.query.filter_by(
        from_school_id=id
    ).all()

    return render_template(
        'transpo_cost_crud.html',
        form=form,
        school=school,
        costs=costs
    )


@app.route('/schools/<int:id>/routes', methods=['GET', 'POST'])
@login_required
def school_routes(id):
    source = db.get_or_404(School, id)
    schools = School.query.order_by(School.id).all()

    graph = {}
    names = {}

    for school in schools:
        graph[school.id] = {}
        names[school.id] = school.name

    costs = TransportationCost.query.all()

    for cost in costs:
        if cost.from_school_id in graph and cost.to_school_id in graph:
            graph[cost.from_school_id][cost.to_school_id] = cost.cost

    distances, paths = sp.dijkstra(graph, id)
    routes = []

    for school in schools:
        if school.id == id:
            continue

        route = {}
        route['school'] = school

        if school.id in paths:
            route['cost'] = distances[school.id]
            route_ids = paths[school.id] + [school.id]
            route_names = []

            for school_id in route_ids:
                route_names.append(names[school_id])

            route['path'] = ' → '.join(route_names)
        else:
            route['cost'] = None
            route['path'] = 'No route available'

        routes.append(route)

    return render_template(
        'routes.html',
        source=source,
        routes=routes
    )