import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    '''
    Paginates and formats questions 
    '''

    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [q.format() for q in selection]
    ans = questions[start:end]

    return ans


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    '''
  Set up CORS. Allow '*' for origins
  '''
    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

    '''
  Use the after_request decorator to set Access-Control-Allow
  '''
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PATCH,POST,DELETE,OPTIONS')
        return response

    '''
  An endpoint to handle GET requests
  for all available categories.
  '''
    @app.route('/categories', methods=['GET'])
    def get_categories():
        categories = Category.query.order_by(Category.id).all()

        if len(categories) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'categories': {category.id: category.type for category in categories},
        })

    '''
  An endpoint to handle GET requests for questions,
  including pagination (every 10 questions).
  This endpoint should return a list of questions,
  number of total questions, current category, categories.

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions.
  '''
    @app.route('/questions', methods=['GET'])
    def get_questions():
        '''
        Return paginated questions
        '''

        q_set = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, q_set)

        categories = Category.query.all()

        if len(current_questions) == 0:
            return jsonify({
                'success': False,
                'message': 'resource not found',
            })

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(q_set),
            'categories': {c.id: c.type for c in categories},
            'current_category': None
        })

    '''
  An endpoint to DELETE question using a question ID.

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page.
  '''
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            refreshed_set = Question.query.order_by(Question.id).all()
            current_set = paginate_questions(request, refreshed_set)

            return jsonify({
                'success': True,
                'deleted': question_id,
                'questions': current_set,
                'total_questions': len(Question.query.all())
            })

        except:
            abort(422)

    '''
  An endpoint to POST a new question,
  which will require the question and answer text,
  category, and difficulty score.
  TEST: When you submit a question on the "Add" tab,
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.
  '''

    @app.route("/questions", methods=['POST'])
    def add_question():
        '''
          Add question
        '''
        body = request.get_json()

        if not ('question' in body and 'answer' in body and
                'difficulty' in body and 'category' in body):
            abort(422)

        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_difficulty = body.get('difficulty', None)
        new_category = body.get('category', None)

        try:
            question = Question(question=new_question, answer=new_answer,
                                difficulty=new_difficulty, category=new_category)
            question.insert()
            return jsonify({
                'success': True,
                'created': question.id,
            })
        except:
            abort(422)

    '''
  An POST endpoint to get questions based on a search term.
  It should return any questions for whom the search term
  is a substring of the question.

  TEST: Search by any phrase. The questions list will update to include
  only question that include that string within their question.
  Try using the word "title" to start.
  '''
    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        '''
          Search questions by key words
        '''
        body = request.get_json()
        search = body.get('searchTerm', None)
        try:
            if search:
                questions = Question.query.order_by(Question.id).filter(
                    Question.question.ilike('%{}%'.format(search)))

                current_category = [
                    q.category for q in questions]

                return jsonify({
                    'success': True,
                    'questions': [q.format() for q in questions.all()],
                    'total_questions': len(questions.all()),
                    'current_category': current_category
                })
            else:
                abort(404)
        except:
            abort(404)

    '''
  An GET endpoint to get questions based on category.

  TEST: In the "List" tab / main screen, clicking on one of the
  categories in the left column will cause only questions of that
  category to be shown.
  '''
    @app.route('/categories/<int:category_id>/questions')
    def get_questions_by_category(category_id):
        '''
          Get questions by category id
        '''
        try:

            questions = Question.query.order_by(Question.id).filter(
                Question.category == str(category_id)
            ).all()
            current_category = [q.category for q in questions]

            if len(questions) == 0:
                abort(404)

            return jsonify({
                'success': True,
                'questions': [question.format() for question in questions],
                'total_questions': len(questions),
                'current_category': category_id
            })

        except:
            abort(404)

    '''
  An POST endpoint to get questions to play the quiz.
  This endpoint should take category and previous question parameters
  and return a random questions within the given category,
  if provided, and that is not one of the previous questions.

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not.
  '''
    @app.route('/quizzes', methods=['POST'])
    def play_quiz():
        """
        Play quiz by returning a new random question
        """
        body = request.get_json()

        previous_questions = body.get('previous_questions', None)
        quiz_category = body.get('quiz_category', None)

        try:
            if quiz_category['type'] == 'click':
                # Collection questions in selected category that aren't in previous questions list

                questions = Question.query.filter(
                    Question.id.notin_((previous_questions))).all()

            else:

                questions = Question.query.filter_by(category=quiz_category['id']).filter(
                    Question.id.notin_((previous_questions))).all()

            if len(questions) > 0:
                question = random.choice(questions).format()

                result = {
                    'success': True,
                    'question': question
                }

            else:
                result = {
                    'success': True,
                    'question': None
                }

            return jsonify(result)

        except:
            abort(422)

    ''' 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 404,
            'message': 'Not Found'
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            'error': 422,
            'message': 'Unprocessable'
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 400,
            'message': 'Bad Request'
        }), 400

    @app.errorhandler(500)
    def sever_error(error):
        return jsonify({
            'error': 500,
            'message': 'Sever Error'
        }), 500

    return app
