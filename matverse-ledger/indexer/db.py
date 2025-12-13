from sqlalchemy import BigInteger, Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Pose(Base):
    __tablename__ = "pose"
    id = Column(Integer, primary_key=True)
    claim_hash = Column(String, index=True)
    submitter = Column(String)
    metadata_uri = Column(String)
    proof_hash = Column(String)
    block_number = Column(BigInteger)
    tx_hash = Column(String)
    timestamp = Column(BigInteger)

class Pole(Base):
    __tablename__ = "pole"
    claim_hash = Column(String, primary_key=True)
    run_hash = Column(String, primary_key=True)
    submitter = Column(String)
    verdict = Column(Integer)
    omega_u6 = Column(BigInteger)
    psi_u6 = Column(BigInteger)
    cvar_u6 = Column(BigInteger)
    latency_ms = Column(BigInteger)
    block_number = Column(BigInteger)
    tx_hash = Column(String)
    timestamp = Column(BigInteger)

def init_db(path: str):
    eng = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(eng)
    return sessionmaker(bind=eng)
