"""
QS MARKETPLACE — Main Application
"""
import os, json
from datetime import datetime, date
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import config

# ── App Setup ────────────────────────────────────────────────
app = Flask(__name__)
app.config['SECRET_KEY']          = config.SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = config.DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER']       = config.UPLOAD_FOLDER
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs("/tmp/database", exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# ════════════════════════════════════════════════════════════
#  MODELS
# ════════════════════════════════════════════════════════════

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role          = db.Column(db.String(20), nullable=False)
    first_name    = db.Column(db.String(80))
    last_name     = db.Column(db.String(80))
    phone         = db.Column(db.String(30))
    location      = db.Column(db.String(120))
    bio           = db.Column(db.Text)
    avatar        = db.Column(db.String(200), default='default.png')
    status        = db.Column(db.String(20), default='pending')
    verified      = db.Column(db.Boolean, default=False)
    joined_at     = db.Column(db.DateTime, default=datetime.utcnow)
    last_login    = db.Column(db.DateTime)

    company_name      = db.Column(db.String(150))
    specialization    = db.Column(db.String(200))
    years_experience  = db.Column(db.Integer)
    certifications    = db.Column(db.Text)
    hourly_rate       = db.Column(db.Float)

    projects_posted   = db.relationship('Project', foreign_keys='Project.client_id', backref='client', lazy=True)
    bids              = db.relationship('Bid', backref='qs_user', lazy=True)
    materials         = db.relationship('Material', backref='vendor', lazy=True)
    sent_messages     = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy=True)
    transactions      = db.relationship('Transaction', foreign_keys='Transaction.user_id', backref='user', lazy=True)

    def set_password(self, pw): self.password_hash = generate_password_hash(pw)
    def check_password(self, pw): return check_password_hash(self.password_hash, pw)
    @property
    def full_name(self): return f"{self.first_name or ''} {self.last_name or ''}".strip() or self.email


class Project(db.Model):
    __tablename__ = 'projects'
    id          = db.Column(db.Integer, primary_key=True)
    client_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    location    = db.Column(db.String(120))
    budget      = db.Column(db.Float)
    deadline    = db.Column(db.Date)
    category    = db.Column(db.String(80))
    status      = db.Column(db.String(30), default='open')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    assigned_qs = db.Column(db.Integer, db.ForeignKey('users.id'))
    bids        = db.relationship('Bid', backref='project', lazy=True)
    transactions= db.relationship('Transaction', backref='project', lazy=True)


class Bid(db.Model):
    __tablename__ = 'bids'
    id          = db.Column(db.Integer, primary_key=True)
    project_id  = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    qs_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount      = db.Column(db.Float, nullable=False)
    proposal    = db.Column(db.Text)
    status      = db.Column(db.String(20), default='pending')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


class Material(db.Model):
    __tablename__ = 'materials'
    id          = db.Column(db.Integer, primary_key=True)
    vendor_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name        = db.Column(db.String(150), nullable=False)
    category    = db.Column(db.String(80))
    description = db.Column(db.Text)
    unit        = db.Column(db.String(30))
    price       = db.Column(db.Float, nullable=False)
    stock       = db.Column(db.Integer, default=0)
    location    = db.Column(db.String(120))
    image       = db.Column(db.String(200))
    active      = db.Column(db.Boolean, default=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


class Message(db.Model):
    __tablename__ = 'messages'
    id          = db.Column(db.Integer, primary_key=True)
    sender_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    body        = db.Column(db.Text, nullable=False)
    read        = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    receiver    = db.relationship('User', foreign_keys=[receiver_id])


class Transaction(db.Model):
    __tablename__ = 'transactions'
    id              = db.Column(db.Integer, primary_key=True)
    project_id      = db.Column(db.Integer, db.ForeignKey('projects.id'))
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id'))
    description     = db.Column(db.String(255))
    amount          = db.Column(db.Float, nullable=False)
    commission_rate = db.Column(db.Float, default=config.COMMISSION_RATE)
    commission_amt  = db.Column(db.Float)
    status          = db.Column(db.String(20), default='pending')
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at         = db.Column(db.DateTime)
    notes           = db.Column(db.Text)


class SiteSettings(db.Model):
    __tablename__ = 'site_settings'
    id    = db.Column(db.Integer, primary_key=True)
    key   = db.Column(db.String(80), unique=True)
    value = db.Column(db.Text)


@login_manager.user_loader
def load_user(uid): return User.query.get(int(uid))

# ════════════════════════════════════════════════════════════
#  SEED DATA
# ════════════════════════════════════════════════════════════

def seed_database():
    if os.path.exists(config.SEED_FLAG_FILE):
        print("  [SEED] Seed flag found — skipping seed.")
        return
    print("  [SEED] Seeding database with sample data…")

    users_data = [
        dict(email='admin@qsmarket.com',    pw='Admin@123',    role='admin',   fn='Platform',   ln='Admin',     phone='+234-800-000-0001', loc='Abuja, Nigeria',      status='active', verified=True,  comp='QS Marketplace HQ'),
        dict(email='client1@example.com',   pw='Client@123',   role='client',  fn='Emeka',      ln='Okafor',    phone='+234-801-234-5678', loc='Lagos, Nigeria',      status='active', verified=True,  comp='Okafor Constructions Ltd'),
        dict(email='client2@example.com',   pw='Client@123',   role='client',  fn='Fatima',     ln='Bello',     phone='+234-802-345-6789', loc='Kano, Nigeria',       status='active', verified=True,  comp='Bello Properties'),
        dict(email='client3@example.com',   pw='Client@123',   role='client',  fn='Chidi',      ln='Nwosu',     phone='+234-803-456-7890', loc='Enugu, Nigeria',      status='pending',verified=False, comp='Nwosu Developers'),
        dict(email='qs1@example.com',       pw='QS@12345',     role='qs',      fn='Adebayo',    ln='Adeleke',   phone='+234-804-567-8901', loc='Lagos, Nigeria',      status='active', verified=True,  spec='Residential & Commercial',   yr=8,  cert='NIQS, RICS', rate=25000),
        dict(email='qs2@example.com',       pw='QS@12345',     role='qs',      fn='Ngozi',      ln='Eze',       phone='+234-805-678-9012', loc='Abuja, Nigeria',      status='active', verified=True,  spec='Infrastructure & Roads',     yr=12, cert='NIQS, AIQS', rate=35000),
        dict(email='qs3@example.com',       pw='QS@12345',     role='qs',      fn='Usman',      ln='Garba',     phone='+234-806-789-0123', loc='Kano, Nigeria',       status='active', verified=True,  spec='Industrial & Oil & Gas',     yr=15, cert='NIQS, RICS, PMP', rate=45000),
        dict(email='qs4@example.com',       pw='QS@12345',     role='qs',      fn='Blessing',   ln='Okonkwo',   phone='+234-807-890-1234', loc='Port Harcourt, NG',   status='pending',verified=False, spec='Residential Projects',       yr=3,  cert='NIQS (Student)', rate=15000),
        dict(email='vendor1@example.com',   pw='Vendor@123',   role='vendor',  fn='Ibrahim',    ln='Musa',      phone='+234-808-901-2345', loc='Lagos, Nigeria',      status='active', verified=True,  comp='Musa Building Materials'),
        dict(email='vendor2@example.com',   pw='Vendor@123',   role='vendor',  fn='Chioma',     ln='Obi',       phone='+234-809-012-3456', loc='Abuja, Nigeria',      status='active', verified=True,  comp='Obi Construction Supplies'),
        dict(email='vendor3@example.com',   pw='Vendor@123',   role='vendor',  fn='Sule',       ln='Ahmed',     phone='+234-810-123-4567', loc='Kano, Nigeria',       status='suspended',verified=True, comp='Ahmed Traders'),
    ]

    created_users = {}
    for u in users_data:
        if User.query.filter_by(email=u['email']).first(): continue
        user = User(
            email=u['email'], role=u['role'],
            first_name=u['fn'], last_name=u['ln'],
            phone=u['phone'], location=u['loc'],
            status=u['status'], verified=u['verified'],
            company_name=u.get('comp'),
            specialization=u.get('spec'),
            years_experience=u.get('yr'),
            certifications=u.get('cert'),
            hourly_rate=u.get('rate'),
            bio=f"Experienced {u['role']} professional based in {u['loc']}.",
            joined_at=datetime.utcnow()
        )
        user.set_password(u['pw'])
        db.session.add(user)
        db.session.flush()
        created_users[u['email']] = user

    db.session.commit()

    admin   = User.query.filter_by(role='admin').first()
    client1 = User.query.filter_by(email='client1@example.com').first()
    client2 = User.query.filter_by(email='client2@example.com').first()
    qs1     = User.query.filter_by(email='qs1@example.com').first()
    qs2     = User.query.filter_by(email='qs2@example.com').first()
    qs3     = User.query.filter_by(email='qs3@example.com').first()
    vendor1 = User.query.filter_by(email='vendor1@example.com').first()
    vendor2 = User.query.filter_by(email='vendor2@example.com').first()

    if not client1 or not qs1:
        db.session.commit()
        open(config.SEED_FLAG_FILE, 'w').write('seeded')
        return

    projects_seed = [
        dict(cid=client1.id, title='5-Bedroom Duplex — Lekki Phase 1',      desc='Complete QS services for a luxury 5-bedroom duplex including BOQ preparation, cost planning and project monitoring.', loc='Lekki, Lagos', budget=8500000, cat='Residential',     status='open',        dl=date(2025,3,30)),
        dict(cid=client1.id, title='Office Complex — Victoria Island',        desc='6-storey commercial office complex. Full QS services from inception to completion required.', loc='Victoria Island, Lagos', budget=45000000, cat='Commercial',      status='in_progress', dl=date(2025,6,15), aqs=qs2.id),
        dict(cid=client2.id, title='Shopping Mall — Kano City Centre',        desc='Large retail shopping mall with 120 shops. BOQ, tendering and contract management needed.', loc='Kano, Nigeria', budget=120000000, cat='Commercial',     status='in_progress', dl=date(2025,9,1),  aqs=qs3.id),
        dict(cid=client2.id, title='Estate Road Network — Abuja',             desc='2.4km internal road network for a new residential estate. QS services including material scheduling.', loc='Abuja, Nigeria', budget=18000000, cat='Infrastructure', status='open',        dl=date(2025,4,20)),
        dict(cid=client1.id, title='Hospital Renovation — Surulere',          desc='Complete renovation of a 40-bed private hospital. Detailed cost estimate and BOQ required.', loc='Surulere, Lagos', budget=22000000, cat='Healthcare',     status='completed',   dl=date(2024,12,31),aqs=qs1.id),
    ]
    proj_objs = []
    for p in projects_seed:
        proj = Project(
            client_id=p['cid'], title=p['title'], description=p['desc'],
            location=p['loc'], budget=p['budget'], category=p['cat'],
            status=p['status'], deadline=p['dl'],
            assigned_qs=p.get('aqs'), created_at=datetime.utcnow()
        )
        db.session.add(proj)
        proj_objs.append(proj)
    db.session.flush()

    proj1, proj2, proj3, proj4, proj5 = proj_objs

    bids_seed = [
        dict(pid=proj1.id, qid=qs1.id, amt=420000,  prop='I will deliver a comprehensive BOQ with market pricing within 10 working days.', status='pending'),
        dict(pid=proj1.id, qid=qs2.id, amt=550000,  prop='15 years experience in luxury residential. Full service including cost monitoring.', status='pending'),
        dict(pid=proj2.id, qid=qs2.id, amt=1800000, prop='Accepted bid for office complex. Full QS service package.', status='accepted'),
        dict(pid=proj3.id, qid=qs3.id, amt=4500000, prop='Comprehensive mall QS service, internationally certified.', status='accepted'),
        dict(pid=proj4.id, qid=qs1.id, amt=720000,  prop='Infrastructure road works specialist. Detailed material schedule included.', status='pending'),
        dict(pid=proj4.id, qid=qs2.id, amt=850000,  prop='Road network BOQ with full cost plan and monitoring.', status='pending'),
        dict(pid=proj5.id, qid=qs1.id, amt=980000,  prop='Hospital renovation specialist. Completed successfully.', status='accepted'),
    ]
    for b in bids_seed:
        bid = Bid(project_id=b['pid'], qs_id=b['qid'], amount=b['amt'], proposal=b['prop'], status=b['status'], created_at=datetime.utcnow())
        db.session.add(bid)

    mats_seed = [
        dict(vid=vendor1.id, name='Dangote 3X Cement',         cat='Cement',       unit='50kg bag', price=8500,   stock=5000, desc='Premium quality cement for all construction purposes.'),
        dict(vid=vendor1.id, name='Iron Rod 16mm (Y16)',        cat='Steel',        unit='per ton',  price=680000, stock=200,  desc='High tensile reinforcement steel rods.'),
        dict(vid=vendor1.id, name='Hollow Blocks (9 inches)',   cat='Blocks',       unit='per piece',price=650,    stock=50000,desc='Standard hollow sandcrete blocks, 9 inches.'),
        dict(vid=vendor1.id, name='Sharp Sand',                 cat='Aggregates',   unit='per ton',  price=18000,  stock=500,  desc='Washed sharp sand for concrete works.'),
        dict(vid=vendor1.id, name='Granite (3/4 inch)',         cat='Aggregates',   unit='per ton',  price=28000,  stock=300,  desc='Crushed granite aggregate for structural concrete.'),
        dict(vid=vendor2.id, name='Aluminium Roofing Sheet',    cat='Roofing',      unit='per sheet',price=7200,   stock=2000, desc='Long span aluminium roofing, 0.55mm thickness.'),
        dict(vid=vendor2.id, name='PVC Pipe 4 inch',            cat='Plumbing',     unit='per length',price=3500,  stock=1500, desc='UPVC pressure pipe for drainage.'),
        dict(vid=vendor2.id, name='Ceramic Floor Tile 60x60',   cat='Tiles',        unit='per m2',   price=4800,   stock=800,  desc='Premium ceramic floor tiles, various colours.'),
        dict(vid=vendor2.id, name='Plaster of Paris (POP)',     cat='Finishing',    unit='per bag',  price=6200,   stock=400,  desc='High quality plaster of paris for ceiling and walls.'),
        dict(vid=vendor2.id, name='Emulsion Paint (20 litres)', cat='Paint',        unit='per tin',  price=28000,  stock=300,  desc='Washable interior/exterior emulsion paint.'),
    ]
    for m in mats_seed:
        mat = Material(vendor_id=m['vid'], name=m['name'], category=m['cat'], unit=m['unit'],
                       price=m['price'], stock=m['stock'], description=m['desc'], location='Lagos, Nigeria',
                       active=True, created_at=datetime.utcnow())
        db.session.add(mat)

    txns_seed = [
        dict(pid=proj2.id, uid=qs2.id,     desc='QS Service Fee — Office Complex VI',     amt=1800000, rate=5.0, status='paid'),
        dict(pid=proj3.id, uid=qs3.id,     desc='QS Service Fee — Shopping Mall Kano',    amt=4500000, rate=5.0, status='pending'),
        dict(pid=proj5.id, uid=qs1.id,     desc='QS Service Fee — Hospital Renovation',   amt=980000,  rate=5.0, status='paid'),
        dict(pid=None,     uid=vendor1.id, desc='Material Sales Commission — Cement',      amt=425000,  rate=5.0, status='paid'),
        dict(pid=None,     uid=vendor2.id, desc='Material Sales Commission — Roofing',     amt=216000,  rate=5.0, status='pending'),
        dict(pid=None,     uid=vendor1.id, desc='Material Sales Commission — Steel',       amt=340000,  rate=5.0, status='overdue'),
    ]
    for t in txns_seed:
        comm = round(t['amt'] * t['rate'] / 100, 2)
        txn = Transaction(project_id=t['pid'], user_id=t['uid'], description=t['desc'],
                          amount=t['amt'], commission_rate=t['rate'], commission_amt=comm,
                          status=t['status'], created_at=datetime.utcnow(),
                          paid_at=datetime.utcnow() if t['status']=='paid' else None)
        db.session.add(txn)

    msgs = [
        dict(sid=client1.id, rid=qs1.id,    body='Hello Adebayo, I saw your profile and I am interested in your services for my Lekki project.'),
        dict(sid=qs1.id,     rid=client1.id, body='Hello Emeka, thank you for reaching out. I would be happy to discuss the Lekki duplex project with you.'),
        dict(sid=client2.id, rid=qs3.id,    body='We have reviewed your bid for the shopping mall. Can we schedule a site visit?'),
        dict(sid=qs3.id,     rid=client2.id, body='Absolutely Fatima. I am available this week. Please share the site address and preferred date.'),
    ]
    for m in msgs:
        msg = Message(sender_id=m['sid'], receiver_id=m['rid'], body=m['body'], created_at=datetime.utcnow())
        db.session.add(msg)

    settings = [
        ('commission_rate', str(config.COMMISSION_RATE)),
        ('site_name', 'QS Marketplace'),
        ('site_tagline', 'Connecting Clients, Quantity Surveyors & Vendors'),
        ('allow_registration', 'true'),
    ]
    for k, v in settings:
        if not SiteSettings.query.filter_by(key=k).first():
            db.session.add(SiteSettings(key=k, value=v))

    db.session.commit()
    open(config.SEED_FLAG_FILE, 'w').write('seeded')
    print("  [SEED] Done! Sample data loaded successfully.")


# ════════════════════════════════════════════════════════════
#  INITIALISE DATABASE (runs on Vercel cold start)
# ════════════════════════════════════════════════════════════

with app.app_context():
    db.create_all()
    seed_database()


# ════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════

def get_setting(key, default=''):
    s = SiteSettings.query.filter_by(key=key).first()
    return s.value if s else default

def unread_count():
    if current_user.is_authenticated:
        return Message.query.filter_by(receiver_id=current_user.id, read=False).count()
    return 0

@app.context_processor
def inject_globals():
    return dict(unread=unread_count, now=datetime.utcnow())

# ════════════════════════════════════════════════════════════
#  AUTH ROUTES
# ════════════════════════════════════════════════════════════

@app.route('/')
def index():
    stats = dict(
        qs_count=User.query.filter_by(role='qs', verified=True, status='active').count(),
        client_count=User.query.filter_by(role='client', status='active').count(),
        vendor_count=User.query.filter_by(role='vendor', status='active').count(),
        project_count=Project.query.filter_by(status='open').count(),
    )
    featured_qs = User.query.filter_by(role='qs', status='active', verified=True).limit(3).all()
    recent_projects = Project.query.filter_by(status='open').order_by(Project.created_at.desc()).limit(4).all()
    return render_template('index.html', stats=stats, featured_qs=featured_qs, recent_projects=recent_projects)

@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if user.status == 'suspended':
                flash('Your account has been suspended. Please contact admin.', 'error')
                return redirect(url_for('login'))
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email     = request.form.get('email','').strip().lower()
        password  = request.form.get('password','')
        role      = request.form.get('role','client')
        fn        = request.form.get('first_name','')
        ln        = request.form.get('last_name','')
        phone     = request.form.get('phone','')
        location  = request.form.get('location','')
        company   = request.form.get('company_name','')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
        elif len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
        else:
            user = User(email=email, role=role, first_name=fn, last_name=ln,
                        phone=phone, location=location, company_name=company,
                        status='pending', verified=False)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Awaiting admin verification.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# ════════════════════════════════════════════════════════════
#  DASHBOARD
# ════════════════════════════════════════════════════════════

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    ctx = {}
    if current_user.role == 'client':
        ctx['my_projects']    = Project.query.filter_by(client_id=current_user.id).order_by(Project.created_at.desc()).all()
        ctx['open_projects']  = [p for p in ctx['my_projects'] if p.status=='open']
        ctx['active_projects']= [p for p in ctx['my_projects'] if p.status=='in_progress']
    elif current_user.role == 'qs':
        ctx['my_bids']        = Bid.query.filter_by(qs_id=current_user.id).order_by(Bid.created_at.desc()).all()
        ctx['open_projects']  = Project.query.filter_by(status='open').order_by(Project.created_at.desc()).limit(6).all()
        ctx['won_bids']       = [b for b in ctx['my_bids'] if b.status=='accepted']
        ctx['my_transactions']= Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.created_at.desc()).limit(5).all()
    elif current_user.role == 'vendor':
        ctx['my_materials']   = Material.query.filter_by(vendor_id=current_user.id).all()
        ctx['active_mats']    = [m for m in ctx['my_materials'] if m.active]
        ctx['my_transactions']= Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.created_at.desc()).limit(5).all()
    ctx['recent_messages'] = Message.query.filter_by(receiver_id=current_user.id, read=False).order_by(Message.created_at.desc()).limit(5).all()
    return render_template('dashboard.html', **ctx)

# ════════════════════════════════════════════════════════════
#  PROJECTS
# ════════════════════════════════════════════════════════════

@app.route('/projects')
@login_required
def projects():
    q = request.args.get('q','')
    cat = request.args.get('cat','')
    query = Project.query.filter_by(status='open')
    if q:   query = query.filter(Project.title.ilike(f'%{q}%'))
    if cat: query = query.filter_by(category=cat)
    projects = query.order_by(Project.created_at.desc()).all()
    cats = ['Residential','Commercial','Infrastructure','Industrial','Healthcare','Education','Other']
    return render_template('projects.html', projects=projects, cats=cats, q=q, selected_cat=cat)

@app.route('/projects/new', methods=['GET','POST'])
@login_required
def new_project():
    if current_user.role != 'client':
        flash('Only clients can post projects.', 'error')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        from datetime import datetime as dt
        dl_raw = request.form.get('deadline')
        dl = dt.strptime(dl_raw, '%Y-%m-%d').date() if dl_raw else None
        proj = Project(
            client_id=current_user.id,
            title=request.form.get('title'),
            description=request.form.get('description'),
            location=request.form.get('location'),
            budget=float(request.form.get('budget') or 0),
            category=request.form.get('category'),
            deadline=dl, status='open'
        )
        db.session.add(proj)
        db.session.commit()
        flash('Project posted successfully!', 'success')
        return redirect(url_for('project_detail', pid=proj.id))
    cats = ['Residential','Commercial','Infrastructure','Industrial','Healthcare','Education','Other']
    return render_template('new_project.html', cats=cats)

@app.route('/projects/<int:pid>')
@login_required
def project_detail(pid):
    proj = Project.query.get_or_404(pid)
    bids = Bid.query.filter_by(project_id=pid).all()
    my_bid = Bid.query.filter_by(project_id=pid, qs_id=current_user.id).first() if current_user.role=='qs' else None
    return render_template('project_detail.html', proj=proj, bids=bids, my_bid=my_bid)

@app.route('/projects/<int:pid>/bid', methods=['POST'])
@login_required
def place_bid(pid):
    if current_user.role != 'qs':
        flash('Only QS professionals can place bids.', 'error')
        return redirect(url_for('project_detail', pid=pid))
    if current_user.status != 'active' or not current_user.verified:
        flash('Your account must be verified and active to place bids.', 'error')
        return redirect(url_for('project_detail', pid=pid))
    existing = Bid.query.filter_by(project_id=pid, qs_id=current_user.id).first()
    if existing:
        flash('You have already placed a bid on this project.', 'error')
        return redirect(url_for('project_detail', pid=pid))
    bid = Bid(project_id=pid, qs_id=current_user.id,
              amount=float(request.form.get('amount',0)),
              proposal=request.form.get('proposal',''))
    db.session.add(bid)
    db.session.commit()
    flash('Bid submitted successfully!', 'success')
    return redirect(url_for('project_detail', pid=pid))

@app.route('/projects/<int:pid>/accept_bid/<int:bid_id>', methods=['POST'])
@login_required
def accept_bid(pid, bid_id):
    proj = Project.query.get_or_404(pid)
    if proj.client_id != current_user.id:
        flash('Unauthorized.', 'error')
        return redirect(url_for('project_detail', pid=pid))
    bid = Bid.query.get_or_404(bid_id)
    Bid.query.filter_by(project_id=pid).update({'status':'rejected'})
    bid.status = 'accepted'
    proj.status = 'in_progress'
    proj.assigned_qs = bid.qs_id
    comm = round(bid.amount * config.COMMISSION_RATE / 100, 2)
    txn = Transaction(project_id=pid, user_id=bid.qs_id,
                      description=f'QS Service Fee — {proj.title}',
                      amount=bid.amount, commission_rate=config.COMMISSION_RATE,
                      commission_amt=comm, status='pending')
    db.session.add(txn)
    db.session.commit()
    flash('Bid accepted! Project is now in progress.', 'success')
    return redirect(url_for('project_detail', pid=pid))

# ════════════════════════════════════════════════════════════
#  QS DIRECTORY
# ════════════════════════════════════════════════════════════

@app.route('/qs-directory')
def qs_directory():
    q    = request.args.get('q','')
    spec = request.args.get('spec','')
    loc  = request.args.get('loc','')
    query = User.query.filter_by(role='qs', status='active', verified=True)
    if q:    query = query.filter(
        (User.first_name.ilike(f'%{q}%')) |
        (User.last_name.ilike(f'%{q}%'))  |
        (User.specialization.ilike(f'%{q}%')))
    if spec: query = query.filter(User.specialization.ilike(f'%{spec}%'))
    if loc:  query = query.filter(User.location.ilike(f'%{loc}%'))
    qs_list = query.all()
    return render_template('qs_directory.html', qs_list=qs_list, q=q, spec=spec, loc=loc)

@app.route('/qs/<int:uid>')
def qs_profile(uid):
    qs = User.query.filter_by(id=uid, role='qs').first_or_404()
    won_projects = Project.query.filter_by(assigned_qs=uid).all()
    return render_template('qs_profile.html', qs=qs, won_projects=won_projects)

# ════════════════════════════════════════════════════════════
#  MATERIALS MARKETPLACE
# ════════════════════════════════════════════════════════════

@app.route('/materials')
def materials():
    q   = request.args.get('q','')
    cat = request.args.get('cat','')
    query = Material.query.filter_by(active=True)
    if q:   query = query.filter(Material.name.ilike(f'%{q}%'))
    if cat: query = query.filter_by(category=cat)
    mats = query.order_by(Material.created_at.desc()).all()
    cats = ['Cement','Steel','Blocks','Aggregates','Roofing','Plumbing','Tiles','Finishing','Paint','Electrical','Other']
    return render_template('materials.html', mats=mats, cats=cats, q=q, selected_cat=cat)

@app.route('/materials/new', methods=['GET','POST'])
@login_required
def new_material():
    if current_user.role != 'vendor':
        flash('Only vendors can list materials.', 'error')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        mat = Material(
            vendor_id=current_user.id,
            name=request.form.get('name'),
            category=request.form.get('category'),
            description=request.form.get('description'),
            unit=request.form.get('unit'),
            price=float(request.form.get('price',0)),
            stock=int(request.form.get('stock',0)),
            location=request.form.get('location', current_user.location),
            active=True
        )
        db.session.add(mat)
        db.session.commit()
        flash('Material listed successfully!', 'success')
        return redirect(url_for('dashboard'))
    cats = ['Cement','Steel','Blocks','Aggregates','Roofing','Plumbing','Tiles','Finishing','Paint','Electrical','Other']
    return render_template('new_material.html', cats=cats)

@app.route('/materials/<int:mid>/toggle', methods=['POST'])
@login_required
def toggle_material(mid):
    mat = Material.query.get_or_404(mid)
    if mat.vendor_id != current_user.id and current_user.role != 'admin':
        flash('Unauthorized.', 'error')
        return redirect(url_for('materials'))
    mat.active = not mat.active
    db.session.commit()
    return redirect(url_for('dashboard'))

# ════════════════════════════════════════════════════════════
#  MESSAGING
# ════════════════════════════════════════════════════════════

@app.route('/messages')
@login_required
def messages():
    received = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.created_at.desc()).all()
    sent     = Message.query.filter_by(sender_id=current_user.id).order_by(Message.created_at.desc()).all()
    Message.query.filter_by(receiver_id=current_user.id, read=False).update({'read': True})
    db.session.commit()
    return render_template('messages.html', received=received, sent=sent)

@app.route('/messages/send', methods=['POST'])
@login_required
def send_message():
    receiver_id = int(request.form.get('receiver_id',0))
    body = request.form.get('body','').strip()
    if not body or not receiver_id:
        flash('Message cannot be empty.', 'error')
    else:
        msg = Message(sender_id=current_user.id, receiver_id=receiver_id, body=body)
        db.session.add(msg)
        db.session.commit()
        flash('Message sent!', 'success')
    return redirect(request.referrer or url_for('messages'))

# ════════════════════════════════════════════════════════════
#  PROFILE
# ════════════════════════════════════════════════════════════

@app.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.first_name       = request.form.get('first_name', current_user.first_name)
        current_user.last_name        = request.form.get('last_name', current_user.last_name)
        current_user.phone            = request.form.get('phone', current_user.phone)
        current_user.location         = request.form.get('location', current_user.location)
        current_user.bio              = request.form.get('bio', current_user.bio)
        current_user.company_name     = request.form.get('company_name', current_user.company_name)
        if current_user.role == 'qs':
            current_user.specialization   = request.form.get('specialization', current_user.specialization)
            current_user.years_experience = int(request.form.get('years_experience') or current_user.years_experience or 0)
            current_user.certifications   = request.form.get('certifications', current_user.certifications)
            current_user.hourly_rate      = float(request.form.get('hourly_rate') or current_user.hourly_rate or 0)
        pw = request.form.get('new_password','')
        if pw and len(pw) >= 6:
            current_user.set_password(pw)
            flash('Password updated.', 'success')
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html')

# ════════════════════════════════════════════════════════════
#  ADMIN ROUTES
# ════════════════════════════════════════════════════════════

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    stats = dict(
        total_users       = User.query.count(),
        pending_users     = User.query.filter_by(status='pending').count(),
        active_users      = User.query.filter_by(status='active').count(),
        suspended_users   = User.query.filter_by(status='suspended').count(),
        total_projects    = Project.query.count(),
        open_projects     = Project.query.filter_by(status='open').count(),
        active_projects   = Project.query.filter_by(status='in_progress').count(),
        total_transactions= Transaction.query.count(),
        pending_comm      = db.session.query(db.func.sum(Transaction.commission_amt)).filter_by(status='pending').scalar() or 0,
        paid_comm         = db.session.query(db.func.sum(Transaction.commission_amt)).filter_by(status='paid').scalar() or 0,
        overdue_comm      = db.session.query(db.func.sum(Transaction.commission_amt)).filter_by(status='overdue').scalar() or 0,
        total_materials   = Material.query.count(),
    )
    recent_users  = User.query.order_by(User.joined_at.desc()).limit(5).all()
    recent_txns   = Transaction.query.order_by(Transaction.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html', stats=stats, recent_users=recent_users, recent_txns=recent_txns)

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    role   = request.args.get('role','')
    status = request.args.get('status','')
    q      = request.args.get('q','')
    query  = User.query
    if role:   query = query.filter_by(role=role)
    if status: query = query.filter_by(status=status)
    if q:      query = query.filter(
        (User.email.ilike(f'%{q}%')) |
        (User.first_name.ilike(f'%{q}%')) |
        (User.last_name.ilike(f'%{q}%')))
    users = query.order_by(User.joined_at.desc()).all()
    return render_template('admin/users.html', users=users, role=role, status=status, q=q)

@app.route('/admin/users/<int:uid>/action', methods=['POST'])
@login_required
@admin_required
def admin_user_action(uid):
    user   = User.query.get_or_404(uid)
    action = request.form.get('action')
    if user.role == 'admin' and action != 'note':
        flash('Cannot modify admin accounts.', 'error')
        return redirect(url_for('admin_users'))
    if action == 'verify':
        user.verified = True
        user.status   = 'active'
        flash(f'{user.full_name} verified and activated.', 'success')
    elif action == 'activate':
        user.status = 'active'
        flash(f'{user.full_name} activated.', 'success')
    elif action == 'suspend':
        user.status = 'suspended'
        flash(f'{user.full_name} suspended.', 'warning')
    elif action == 'delete':
        db.session.delete(user)
        db.session.commit()
        flash('User deleted permanently.', 'info')
        return redirect(url_for('admin_users'))
    db.session.commit()
    return redirect(request.referrer or url_for('admin_users'))

@app.route('/admin/transactions')
@login_required
@admin_required
def admin_transactions():
    status = request.args.get('status','')
    query  = Transaction.query
    if status: query = query.filter_by(status=status)
    txns = query.order_by(Transaction.created_at.desc()).all()
    total_comm = sum(t.commission_amt or 0 for t in txns)
    return render_template('admin/transactions.html', txns=txns, total_comm=total_comm, status=status)

@app.route('/admin/transactions/<int:tid>/action', methods=['POST'])
@login_required
@admin_required
def admin_txn_action(tid):
    txn    = Transaction.query.get_or_404(tid)
    action = request.form.get('action')
    if action == 'mark_paid':
        txn.status  = 'paid'
        txn.paid_at = datetime.utcnow()
        flash('Transaction marked as paid.', 'success')
    elif action == 'mark_overdue':
        txn.status = 'overdue'
        flash('Transaction marked as overdue.', 'warning')
    elif action == 'mark_disputed':
        txn.status = 'disputed'
        flash('Transaction marked as disputed.', 'info')
    txn.notes = request.form.get('notes', txn.notes)
    db.session.commit()
    return redirect(url_for('admin_transactions'))

@app.route('/admin/projects')
@login_required
@admin_required
def admin_projects():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('admin/projects.html', projects=projects)

@app.route('/admin/settings', methods=['GET','POST'])
@login_required
@admin_required
def admin_settings():
    if request.method == 'POST':
        commission = request.form.get('commission_rate')
        if commission:
            s = SiteSettings.query.filter_by(key='commission_rate').first()
            if s: s.value = commission
            else: db.session.add(SiteSettings(key='commission_rate', value=commission))
            config.COMMISSION_RATE = float(commission)
        db.session.commit()
        flash('Settings updated.', 'success')
        return redirect(url_for('admin_settings'))
    settings = {s.key: s.value for s in SiteSettings.query.all()}
    return render_template('admin/settings.html', settings=settings)

@app.route('/admin/database', methods=['GET','POST'])
@login_required
@admin_required
def admin_database():
    seed_exists = os.path.exists(config.SEED_FLAG_FILE)
    db_path     = "/tmp/marketplace.db"
    db_size     = round(os.path.getsize(db_path) / 1024, 1) if os.path.exists(db_path) else 0
    counts = dict(
        users=User.query.count(), projects=Project.query.count(),
        bids=Bid.query.count(), materials=Material.query.count(),
        messages=Message.query.count(), transactions=Transaction.query.count(),
    )
    return render_template('admin/database.html', seed_exists=seed_exists, db_size=db_size, counts=counts)

@app.route('/admin/database/action', methods=['POST'])
@login_required
@admin_required
def admin_database_action():
    action = request.form.get('action')

    if action == 'reset_database':
        db.drop_all()
        db.create_all()
        if os.path.exists(config.SEED_FLAG_FILE):
            os.remove(config.SEED_FLAG_FILE)
        admin = User(email='admin@qsmarket.com', role='admin', first_name='Platform',
                     last_name='Admin', status='active', verified=True)
        admin.set_password('Admin@123')
        db.session.add(admin)
        db.session.commit()
        flash('Database reset successfully. Admin account recreated. You have been logged out.', 'warning')
        logout_user()
        return redirect(url_for('login'))

    elif action == 'reseed':
        if os.path.exists(config.SEED_FLAG_FILE):
            os.remove(config.SEED_FLAG_FILE)
        seed_database()
        flash('Database re-seeded with sample data.', 'success')

    elif action == 'prevent_seed':
        open(config.SEED_FLAG_FILE, 'w').write('seeded')
        flash('Seed flag set. Database will not be seeded on next run.', 'info')

    elif action == 'allow_seed':
        if os.path.exists(config.SEED_FLAG_FILE):
            os.remove(config.SEED_FLAG_FILE)
        flash('Seed flag removed. Database will seed on next application restart.', 'info')

    return redirect(url_for('admin_database'))

# ════════════════════════════════════════════════════════════
#  ERROR HANDLERS
# ════════════════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500

@app.errorhandler(403)
def forbidden(e):
    return render_template("404.html"), 403

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_database()
    import webbrowser, threading
    threading.Timer(1.5, lambda: webbrowser.open('http://127.0.0.1:5000')).start()
    print("\n" + "="*55)
    print("  QS MARKETPLACE — Running at http://127.0.0.1:5000")
    print("  Admin login: admin@qsmarket.com / Admin@123")
    print("  Press CTRL+C to stop the server")
    print("="*55 + "\n")
    app.run(debug=False, port=5000)
