class Config(PredictedMeBase):
    __tablename__ = 'config'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(String(250), unique=True, nullable=False)


class TagsSetup(PredictedMeBase):
    __tablename__ = 'tags_setup'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    customer_id = Column(ForeignKey('customer_setup.id', ondelete='CASCADE'))
    customer = relationship('CustomerSetup')
    icon = Column(BigInteger, nullable=True)
    show_in_menu = Column(Boolean, nullable=False, default=False)
    extract_text = Column(Boolean, nullable=False, default=False)
    extract_numeric_metrics = Column(Boolean, nullable=False, default=False)
    aggregation_function = Column(ENUM('min', 'max', 'avg', 'sum', 'count'), default='avg')
    aggregation_time_units = Column(ENUM('second', 'minute', 'hour', 'day', 'week'), default='day')
    aggregation_step = Column(BigInteger, default=1)
    aggregate = Column(Boolean, nullable=False, default=False)
    internal = Column(Boolean, nullable=False, default=False)


class CustomerSetup(PredictedMeBase):
    __tablename__ = 'customer_setup'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    external_id = Column(String(36), nullable=False, unique=True)
    analytics_ran_last = Column(BigInteger, nullable=True)
    accepted_terms = Column(Boolean, nullable=False, default=True)
    tags = relationship('TagsSetup', lazy=True, cascade="all, delete-orphan")
    uploads = relationship('Upload', lazy=True, cascade="all, delete-orphan")
    rewards = relationship('Reward', lazy=False, cascade="all, delete-orphan")
    purchases = relationship('Purchase', lazy=True, cascade="all, delete-orphan")
    device_token = Column(String(100), nullable=True, unique=True)
    seconds_left = Column(Float, nullable=False, default=0)
    bytes_left = Column(Float, nullable=False, default=0)
    words_left = Column(Float, nullable=False, default=0)
    analytics_left = Column(Float, nullable=False, default=0)
    predictions_left = Column(Float, nullable=False, default=0)
    csv_left = Column(Float, nullable=False, default=0)
    parent_customer_id = Column(ForeignKey('customer_setup.id', ondelete='CASCADE'), nullable=True)
    parent_customer = relationship('CustomerSetup', lazy=False, uselist=False)
    coupon = Column(String(50), nullable=False, unique=True)
    #
    # created_coupon_id = Column(ForeignKey('coupon.id', ondelete='CASCADE'))
    # created_coupon = relationship('Coupon', lazy=False,  foreign_keys=[created_coupon_id], uselist=False)
    # parent_coupon_id = Column(ForeignKey('coupon.id', ondelete='CASCADE'))
    # parent_coupon = relationship('Coupon', lazy=False, foreign_keys=[parent_coupon_id], uselist=False)


class Reward(PredictedMeBase):
    __tablename__ = 'reward'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts = Column(BigInteger, nullable=False)
    percent = Column(String(25), nullable=False)
    seconds_left = Column(Float, nullable=False, default=0)
    bytes_left = Column(Float, nullable=False, default=0)
    words_left = Column(Float, nullable=False, default=0)
    analytics_left = Column(Float, nullable=False, default=0)
    predictions_left = Column(Float, nullable=False, default=0)
    customer_id = Column(ForeignKey('customer_setup.id', ondelete='CASCADE'))
    customer = relationship('CustomerSetup', uselist=False)


# class Coupon(PredictedMeBase):
#     __tablename__ = 'coupon'
#     id = Column(BigInteger, primary_key=True, autoincrement=True)
#     name = Column(String(50), nullable=True)
#     customer_id = Column(ForeignKey('customer_setup.id', ondelete='CASCADE'))
#     customer = relationship('CustomerSetup', foreign_keys='CustomerSetup.created_coupon_id', cascade="all, delete-orphan", uselist=False, lazy=False)
#

MetricsSetupTags = Table(
    'metrics_setup_tags',
    PredictedMeBase.metadata,
    Column('metrics_setup_id', ForeignKey('metrics_setup.id', ondelete='CASCADE'), primary_key=True, nullable=False),
    Column('tags_setup_id', ForeignKey('tags_setup.id', ondelete='CASCADE'), primary_key=True, nullable=False)
)

MetricsTags = Table(
    'metrics_tags',
    PredictedMeBase.metadata,
    Column('metrics_id', ForeignKey('metrics.id', ondelete='CASCADE'), primary_key=True, nullable=False),
    Column('tags_setup_id', ForeignKey('tags_setup.id', ondelete='CASCADE'), primary_key=True, nullable=False)
)


class MetricsSetup(PredictedMeBase):
    __tablename__ = 'metrics_setup'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(750), nullable=False)
    customer_id = Column(ForeignKey('customer_setup.id', ondelete='CASCADE'), nullable=False)
    customer = relationship('CustomerSetup')
    units = Column(String(25), nullable=True)
    analytics_enabled = Column(Boolean, nullable=False, default=False)
    tags = relationship('TagsSetup', secondary=MetricsSetupTags, lazy=False)
    recurrent = Column(Boolean, nullable=False, default=False)
    extract_text = Column(Boolean, nullable=False, default=False)
    extract_numeric_metrics = Column(Boolean, nullable=False, default=False)
    aggregation_function = Column(ENUM('min', 'max', 'avg', 'sum', 'count'), default='avg')
    aggregation_time_units = Column(ENUM('second', 'minute', 'hour', 'day', 'week'), default='day')
    aggregation_step = Column(BigInteger, default=1)
    aggregate = Column(Boolean, nullable=False, default=False)
    insights = relationship('Insights', lazy=False)


Index('metrics_setup.customer_metrics', MetricsSetup.name, MetricsSetup.customer_id)


class Metrics(PredictedMeBase):
    __tablename__ = 'metrics'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts = Column(BigInteger, nullable=False)
    metrics_setup_id = Column(ForeignKey('metrics_setup.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    metrics_setup = relationship('MetricsSetup', lazy=False)
    tags = relationship('TagsSetup', secondary=MetricsTags, lazy=False)
    reported_value: Mapped[BigInteger] = Column(BigInteger, nullable=True)
    comment = Column(BLOB)
    media = relationship('MetricsMedia', lazy=False, cascade="all, delete-orphan")
    comment_processed = Column(Boolean, nullable=False, default=False)
    parent_metrics_id = Column(ForeignKey('metrics.id', ondelete='CASCADE'), nullable=True)
    parent_metrics = relationship('Metrics')
    upload_id = Column(ForeignKey('upload.id', ondelete='CASCADE'), nullable=True)
    processing_error = Column(BLOB)


class Upload(PredictedMeBase):
    __tablename__ = 'upload'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uploaded_file: Mapped[String] = Column(String(500), nullable=False)
    customer_id = Column(ForeignKey('customer_setup.id', ondelete='CASCADE'), nullable=True)
    customer = relationship('CustomerSetup')
    status = Column(ENUM('started', 'success', 'has errors', 'failed'), default='started')
    errors_file = Column(String(500))
    error = Column(BLOB)
    errors = relationship('UploadErrors', lazy=True, cascade="all, delete-orphan")
    ts = Column(BigInteger, nullable=False)
    size = Column(BigInteger, nullable=False)


class UploadErrors(PredictedMeBase):
    __tablename__ = 'upload_errors'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    upload_id = Column(ForeignKey('upload.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    data = Column(BLOB)


class MetricsMedia(PredictedMeBase):
    __tablename__ = 'metrics_media'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    metrics_id = Column(ForeignKey('metrics.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    metrics = relationship('Metrics')
    media_url: Mapped[String] = Column(String(500), nullable=False)
    comment = Column(BLOB)
    processed = Column(Boolean, nullable=False, default=False)
    duration = Column(BigInteger, nullable=False, default=0)
    size = Column(BigInteger, nullable=False, default=0)


class Insights(PredictedMeBase):
    __tablename__ = 'metrics_setup_insights'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    metrics_setup_id = Column(ForeignKey('metrics_setup.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    metrics_setup = relationship('MetricsSetup', lazy=False)
    graph_id = Column(ForeignKey('graph.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    graph = relationship('Graph', lazy=False)
    details: Mapped[String] = Column(String(300), nullable=False)
    value: Mapped[Float] = Column(Float, nullable=True)


class Purchase(PredictedMeBase):
    __tablename__ = 'purchases'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    customer_id = Column(ForeignKey('customer_setup.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    customer = relationship('CustomerSetup', lazy=False)
    ts = Column(BigInteger, nullable=False)
    price: Mapped[String] = Column(String(25), nullable=False)
    code: Mapped[String] = Column(String(25), nullable=False)
    plan_id: Mapped[String] = Column(String(25), nullable=False)
    formatted_price: Mapped[String] = Column(String(50), nullable=False)
    title = Column(String(100), nullable=True)


class Series(PredictedMeBase):
    __tablename__ = 'series'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[String] = Column(String(100), nullable=False)
    type = Column(ENUM('metrics', 'tags'))
    aggregation_function = Column(ENUM('min', 'max', 'avg', 'sum', 'count'), default='avg')
    aggregation_time_units = Column(ENUM('second', 'minute', 'hour', 'day', 'week'), default='day')
    aggregation_step = Column(BigInteger, default=1)
    aggregate = Column(Boolean, nullable=False, default=False)
    graph_id = Column('graph_id', ForeignKey('graph.id', ondelete='CASCADE', onupdate='CASCADE'))
    predict = Column(Boolean, nullable=False, default=False)


class Graph(PredictedMeBase):
    __tablename__ = 'graph'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[String] = Column(String(100), nullable=False)
    series = relationship('Series', lazy=False, cascade="all, delete-orphan")
    customer = relationship('CustomerSetup', lazy=True)
    customer_id = Column(ForeignKey('customer_setup.id', ondelete='CASCADE'), nullable=False)
    period_units = Column(ENUM('second', 'minute', 'hour', 'day', 'week'), default='day')
    period_length = Column(BigInteger, default=30)
    predictions_enabled = Column(Boolean, nullable=False, default=False)
    no_edit = Column(Boolean, nullable=False, default=False)
    insights = relationship('Insights', lazy=True)


tables = [Config.__table__,
          TagsSetup.__table__,
          CustomerSetup.__table__,
          MetricsSetup.__table__,
          MetricsSetupTags,
          Metrics.__table__,
          MetricsMedia.__table__,
          Graph.__table__,
          Series.__table__]

ImageMetadata = Table(
    'image_metadata', metadata,
    # Primary Key for idempotency (optional, but good practice)
    Column('s3_key', String(2048), primary_key=True),
    Column('main_description', String(4096)),
    # SQLAlchemy requires a native MySQL type for lists/arrays if using ORM
    # A common non-ORM approach is to store lists as JSON strings:
    Column('detected_objects', String(2048)),  # Stores a JSON string
    Column('activities', String(2048)),  # Stores a JSON string
    Column('image_sentiment', String(255)),
    extend_existing=True
)
