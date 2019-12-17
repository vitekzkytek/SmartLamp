from flask import Flask, request, redirect, Response, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime, Boolean, ForeignKey
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import io

app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////root/arduino/smartlamp/db.sqlite'
app.config['DEBUG'] = True


db = SQLAlchemy(app)

MORSE_CODE_DICT = {
                    'A': '.-', 'B': '-...',
                    'C': '-.-.', 'D': '-..', 'E': '.',
                    'F': '..-.', 'G': '--.', 'H': '....',
                    'I': '..', 'J': '.---', 'K': '-.-',
                    'L': '.-..', 'M': '--', 'N': '-.',
                    'O': '---', 'P': '.--.', 'Q': '--.-',
                    'R': '.-.', 'S': '...', 'T': '-',
                    'U': '..-', 'V': '...-', 'W': '.--',
                    'X': '-..-', 'Y': '-.--', 'Z': '--..',
                    '1': '.----', '2': '..---', '3': '...--',
                    '4': '....-', '5': '.....', '6': '-....',
                    '7': '--...', '8': '---..', '9': '----.',
                    '0': '-----', ' ': '_'
                }


class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(80), unique=False, nullable=False)
    nickname = db.Column(db.String(120), unique=False, nullable=False)
    timestamp = db.Column(DateTime, unique=False, nullable=False)
    isPending = db.Column(Boolean, unique=False, nullable=False)
    forwardedAt = db.Column(DateTime, unique=False, nullable=True)

    def __repr__(self):
        return 'Word %r from %r' % (self.word, self.nickname)


class LampRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(16),unique=False, nullable=False)
    lamp_name = db.Column(db.String(20),unique=False, nullable=True)
    requestedAt = db.Column(DateTime, unique=False, nullable=False)
    responded_word_id = db.Column(db.Integer, ForeignKey(Word.id))

    def __repr__(self):
        return 'Request %r from %r' % (self.ip, self.lamp_name)

@app.route('/')
def index():
    last_vitek = db.session.query(LampRequest).filter(LampRequest.lamp_name == 'vitek').order_by(LampRequest.requestedAt.desc()).first()

    df = pd.read_sql_query('''
        select word,nickname,timestamp from Word
        where isPending = 1
        ''', con=db.engine, parse_dates=['timestamp'])

    html = '''
    <html>
        <head>
            <meta http-equiv="refresh" content="30"/>
            <title>Smart Lamp for Golemio</title>
            <style>
                .column {{
                float: left;
                width: 50%;
                }}

                /* Clear floats after the columns */
                .row:after {{
                content: "";
                display: table;
                clear: both;
                }}

            </style>
        </head>
        <body>
            <h1>Smart Lamp Controller</h1>
            <div class="row">
                <div class="column">
                    <form action="/saveToDB" method='POST'>
                        <div>
                        Vložte text: <input type="text" id="word_in" name="word_in" required></input> !! Cokoliv mimo A-Z a 0-9 bude vymazáno.<br />
                        Kdo jste? <input type="text" id="nickname_in" name="nickname_in" value="" required></input><br />
                        <button type="submit">Submit</button>
                        </div>
                    </form>
                </div>
                <div class="column">
                    <img src="{}" height="200" width="200"/>
                </div>

            </div>
            <div class="row">
                <div class="column">
                    <h3>Word Queue: </h3>
                    <div>
                    {}
                    </div>
                </div>
                <div class="column">
                    <h3>Last seen lamp:</h3>
                    <p>Vítek: {}</p>
                </div>
            </div>
            <h3>Little dashboard</h3>
            <img src="/plot.png" alt="my plot">
        </body>
    </html>
    '''.format(
            url_for('static', filename='lampa_QR.png'),
            df.to_html(formatters={'timestamp': lambda x: x.strftime('%Y-%m-%d %H:%M:%S')}),
            last_vitek.requestedAt.strftime('%Y-%m-%d %H:%M:%S'),
            '')
    return html


@app.route('/truncate_DB')
def truncate_DB():
    db.drop_all()
    db.session.commit()
    db.create_all()
    db.session.commit()
    return redirect('/')



@app.route('/saveToDB', methods=['POST'])
def saveToDB():
    word_in = validate(request.form['word_in'])
    if word_in:
        nickname_in = request.form['nickname_in']
        db_Word = Word(
            word=word_in,
            nickname=nickname_in,
            timestamp=pd.Timestamp.now(),
            isPending=True
        )

        db.session.add(db_Word)
        db.session.commit()
    return redirect('/')


def validate(s):

    return ''.join([ch.upper() for ch in s if ch.upper() in MORSE_CODE_DICT])


@app.route('/gimme_next/<lamp_name>')
def gimme_next(lamp_name):
    lr = LampRequest(
        ip=request.remote_addr,
        requestedAt=pd.Timestamp.now(),
        lamp_name=lamp_name)
    db.session.add(lr)

    try:
        next_word = db.session.query(Word).filter(Word.isPending == 1).order_by(Word.timestamp).first()
        if next_word is not None:
            d_next_word = next_word.__dict__
            d = {key: str(d_next_word[key]) for key in d_next_word.keys() if key != '_sa_instance_state'}

            next_word.forwardedAt = pd.Timestamp.now()
            next_word.isPending = 0
            lr.responded_word_id = next_word.id

            db.session.commit()
            morses = [MORSE_CODE_DICT[char] for char in d['word'].upper()]
            d['morse_list'] = morses
            d['morse_delimiters'] = '_'.join(morses)
            d['result'] = 'success'
            return d
        else:
            db.session.commit()
            return {
                'result': 'null',
                'chyba': 'no word available',
                'timestamp': pd.Timestamp.now()
            }
    except Exception as e:
        return {
            'result': 'null',
            'chyba': str(e),
            'timestamp': pd.Timestamp.now()
        }


@app.route('/plot.png')
def plot_png():
    plt.clf()
    fig = create_figure()
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    figoutput = output.getvalue()
    plt.close('fig')
    return Response(figoutput, mimetype='image/png')

def generateWordCloud(series,ax):
    wordcloud = WordCloud(width=400,
                            height=300, 
                            background_color='white', 
                            stopwords=[], 
                            min_font_size=10
                    ).generate(' '.join([str(word) for word in series])) 
    ax.imshow(wordcloud) 
    ax.set_axis_off() 


def create_figure():
    fig, axs = plt.subplots(nrows=1, ncols=3, figsize=(10, 4))

    words = pd.read_sql_query('select * from word', db.engine, parse_dates=['timestamp','forwardedAt'])
    rqst = pd.read_sql_query('select * from lamp_request', db.engine, parse_dates='requestedAt')
    min_words = words.groupby([pd.Grouper(key='forwardedAt',freq='60s')]).size().rename('# Words forwarded').to_frame()
    min_rqst = rqst.groupby(['lamp_name', pd.Grouper(key='requestedAt', freq='60s')]).size().unstack('lamp_name').rename({'vitek':"Lamp's requests",'hell':"Helena's requests"},axis=1)
    times = min_rqst.merge(min_words, left_index=True, right_index=True, how='outer')
    times.plot(ax=axs[0],marker='o', linewidth=0, ylim=(0.5,15),title='Lamp and User Monitoring')

    generateWordCloud(words.word, axs[1])
    words.groupby('nickname').size().sort_values(ascending=False).plot.bar(ax=axs[2],title='Most active contributors')
    return fig
