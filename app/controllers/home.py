from app import app, db, login_manager
from app.models.topic import Topic
from app.models.issue import Issue
from app.models.voter import Voter
from app.models.user import User
from flask import render_template, request
from flask_login import current_user

@app.route('/')
def index():
    sort = request.args.get('sort', 'top')
    topic = request.args.get('topic')
    if current_user.is_authenticated:
        user_id = current_user.id
        topics = current_user.following_topics
    else:
        user_id = 0
        topics = Topic.query.order_by(
            Topic.group.desc(),
            Topic.issues_count.desc()
        ).limit(10).all()
    terms = db.and_(Voter.target_id==Issue.id, Voter.user_id==user_id)
    case = db.case([(Voter.user_id==user_id, True)], else_=False)
    query = db.session.query(Issue, case.label('has_voted'))
    if topic:
        query = query.filter(Issue.topics.any(Topic.name==topic))
    elif user_id > 0 and len(current_user.following_topics) > 0:
        topic_terms = []
        for t in current_user.following_topics:
            topic_terms.append(Issue.topics.any(Topic.name==t.name))
        query = query.filter(db.or_(*topic_terms))
    if sort == 'top':
        query = query.order_by(Issue.score.desc(), Issue.created_at.desc())
    else:
        query = query.order_by(Issue.created_at.desc())
    query = query.outerjoin(Voter, terms)
    feeds = query.all()
    ctx = {
        'feeds': feeds,
        'topics': topics,
        'navbar_active': 'stories',
        'topic': topic,
        'sort': sort
    }
    return render_template('index.html', **ctx)
