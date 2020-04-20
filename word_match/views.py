import json

from flask import (
    redirect,
    request,
    render_template,
    session
)

from .app import app
from .decorators import require_gamemaster, require_username
from .models import Cardset, Game
from .utils import alphanumeric_only, slug_for_resource

@app.route('/')
def home():
    return render_template('home.html', cardsets=Cardset.all_slugs(), games=Game.all_slugs())


@app.route('/login', methods=['GET','POST'])
def login():
    if request.form.get('username'):
        username = alphanumeric_only(request.form.get('username')).strip()
        if username:
            print(f'{username} is logging in')
            session['username'] = username
    else:
        session.pop('username', None)

    if request.form.get('game_code'):
        code = alphanumeric_only(request.form.get('game_code'))
        if code == app.config['GAMEMASTER_CODE']:
            print(f'User is gamemaster')
            session['is_gamemaster'] = True
        elif session.get('is_gamemaster'):
            session.pop('is_gamemaster', None)
    else:
        session.pop('is_gamemaster', None)

    return redirect('/')

@require_gamemaster
@app.route('/cardsets/create', methods=['POST'])
def cardsets_create():
    upload = request.files.get('cardset-file')
    if upload and upload.filename and upload.filename.endswith('.json'):
        cardset_data = json.load(upload)
        if cardset_data.get('response_cards') and cardset_data.get('prompt_cards'):
            Cardset(
                name=request.form.get('name') or random_string(4),
                prompt_cards=cardset_data['prompt_cards'],
                response_cards=cardset_data['response_cards']
            ).save()
    return redirect('/')

@require_gamemaster
@app.route('/games/create', methods=['POST'])
def create_game():
    slug = slug_for_resource(Game)
    cardset = Cardset.from_slug(request.form.get('cardset'))
    if cardset:
        print(f"Saving game {slug} for cardset {cardset.name}")
        Game(slug=slug, cardset=cardset).save()
    return redirect('/')

@require_username
@app.route('/games/<string:game_slug>')
def play(game_slug):
    safe_slug = alphanumeric_only(game_slug)
    if not Game.slug_exists(safe_slug):
        return redirect('/')

    return render_template('play.html', game=Game.from_slug(safe_slug))

all_loaded = True