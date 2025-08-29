from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from models import db, Student, Grade
from forms import StudentForm, GradeForm
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def create_app():
    app = Flask(__name__)
    # Use a secure secret key in production (set via env var)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'students.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    # ---------- Routes ----------
    @app.route('/')
    def index():
        # Home page: show quick stats & links
        total_students = Student.query.count()
        # compute class average (average of all student averages)
        students = Student.query.all()
        avg_list = [s.average() for s in students if s.has_grades()]
        class_avg = round(sum(avg_list) / len(avg_list), 2) if avg_list else None
        return render_template('index.html', total_students=total_students, class_avg=class_avg)

    @app.route('/students')
    def list_students():
        students = Student.query.order_by(Student.name).all()
        return render_template('list_students.html', students=students)

    @app.route('/student/add', methods=['GET', 'POST'])
    def add_student():
        form = StudentForm(request.form)
        if request.method == 'POST' and form.validate():
            name = form.name.data.strip()
            roll_number = form.roll_number.data.strip()
            # check uniqueness
            existing = Student.query.filter_by(roll_number=roll_number).first()
            if existing:
                flash(f'Roll number "{roll_number}" already exists.', 'danger')
                return render_template('add_student.html', form=form)
            student = Student(name=name, roll_number=roll_number)
            db.session.add(student)
            try:
                db.session.commit()
                flash('Student added successfully.', 'success')
                return redirect(url_for('list_students'))
            except IntegrityError:
                db.session.rollback()
                flash('Error saving student. Try again.', 'danger')
        return render_template('add_student.html', form=form)

    @app.route('/student/<int:student_id>')
    def student_detail(student_id):
        student = Student.query.get_or_404(student_id)
        grades = student.grades  # list of Grade objects
        return render_template('student_detail.html', student=student, grades=grades)

    @app.route('/student/<int:student_id>/add_grades', methods=['GET', 'POST'])
    def add_grades(student_id):
        student = Student.query.get_or_404(student_id)
        form = GradeForm(request.form)
        if request.method == 'POST' and form.validate():
            subject = form.subject.data.strip()
            score = form.score.data
            # ensure 0-100
            score = max(0, min(100, score))
            grade = Grade(subject=subject, score=score, student_id=student.id)
            db.session.add(grade)
            db.session.commit()
            flash('Grade added successfully.', 'success')
            return redirect(url_for('student_detail', student_id=student.id))
        return render_template('add_grades.html', form=form, student=student)

    @app.route('/student/<int:student_id>/delete', methods=['POST'])
    def delete_student(student_id):
        student = Student.query.get_or_404(student_id)
        db.session.delete(student)
        db.session.commit()
        flash('Student deleted.', 'success')
        return redirect(url_for('list_students'))

    @app.route('/student/<int:student_id>/delete_grade/<int:grade_id>', methods=['POST'])
    def delete_grade(student_id, grade_id):
        grade = Grade.query.get_or_404(grade_id)
        db.session.delete(grade)
        db.session.commit()
        flash('Grade deleted.', 'success')
        return redirect(url_for('student_detail', student_id=student_id))

    @app.route('/reports')
    def reports():
        # Generate some quick reports: subject-wise toppers and class averages
        # Subject-wise average and topper
        subjects = db.session.query(Grade.subject).distinct().all()
        subject_reports = []
        for (subject,) in subjects:
            rows = Grade.query.filter_by(subject=subject).all()
            if not rows:
                continue
            avg = round(sum(r.score for r in rows) / len(rows), 2)
            topper = max(rows, key=lambda g: g.score).student  # Student object
            subject_reports.append({
                'subject': subject,
                'average': avg,
                'topper': topper,
                'top_score': max(r.score for r in rows)
            })
        return render_template('report.html', subject_reports=subject_reports)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
