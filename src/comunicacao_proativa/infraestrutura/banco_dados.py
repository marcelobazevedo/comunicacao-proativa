from datetime import UTC, date, datetime
from pathlib import Path

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from comunicacao_proativa.configuracao import Configuracao
from comunicacao_proativa.dominio.entidades import Segurado, TipoApolice


class Base(DeclarativeBase):
    pass


class SeguradoModelo(Base):
    __tablename__ = "segurados"
    identificador: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    cidade: Mapped[str] = mapped_column(String(120), index=True)
    estado: Mapped[str] = mapped_column(String(2), default="SP")
    pais: Mapped[str] = mapped_column(String(2), default="BR")
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    canal_preferido: Mapped[str] = mapped_column(String(20), default="push")
    apolices: Mapped[list["ApoliceModelo"]] = relationship(cascade="all, delete-orphan")


class ApoliceModelo(Base):
    __tablename__ = "apolices"
    identificador: Mapped[int] = mapped_column(primary_key=True)
    segurado_id: Mapped[int] = mapped_column(ForeignKey("segurados.identificador"), index=True)
    tipo: Mapped[str] = mapped_column(String(30))


class ExecucaoModelo(Base):
    __tablename__ = "execucoes"
    identificador: Mapped[int] = mapped_column(primary_key=True)
    iniciada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    concluida_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    modo: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30))
    erro: Mapped[str | None] = mapped_column(Text, nullable=True)


class EventoModelo(Base):
    __tablename__ = "eventos_climaticos"
    identificador: Mapped[int] = mapped_column(primary_key=True)
    execucao_id: Mapped[int] = mapped_column(ForeignKey("execucoes.identificador"), index=True)
    tipo: Mapped[str] = mapped_column(String(40))
    cidade: Mapped[str] = mapped_column(String(120))
    data: Mapped[date] = mapped_column(Date)
    severidade: Mapped[str] = mapped_column(String(20))
    evidencia: Mapped[str] = mapped_column(Text)


class NotificacaoModelo(Base):
    __tablename__ = "notificacoes"
    identificador: Mapped[int] = mapped_column(primary_key=True)
    execucao_id: Mapped[int] = mapped_column(ForeignKey("execucoes.identificador"), index=True)
    segurado_id: Mapped[int] = mapped_column(ForeignKey("segurados.identificador"), index=True)
    tipo_evento: Mapped[str] = mapped_column(String(40))
    apolice: Mapped[str] = mapped_column(String(30))
    mensagem: Mapped[str] = mapped_column(Text)
    provedor_modelo: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30), default="simulada")
    canal: Mapped[str] = mapped_column(String(20), default="push")
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MensagemModelo(Base):
    __tablename__ = "mensagens"
    identificador: Mapped[int] = mapped_column(primary_key=True)
    execucao_id: Mapped[int] = mapped_column(ForeignKey("execucoes.identificador"), index=True)
    segurado_id: Mapped[int] = mapped_column(ForeignKey("segurados.identificador"), index=True)
    tipo_evento: Mapped[str] = mapped_column(String(40))
    conteudo: Mapped[str] = mapped_column(Text)
    provedor_modelo: Mapped[str] = mapped_column(String(80))
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class VerificacaoMeteorologicaModelo(Base):
    __tablename__ = "verificacoes_meteorologicas"
    identificador: Mapped[int] = mapped_column(primary_key=True)
    execucao_id: Mapped[int] = mapped_column(ForeignKey("execucoes.identificador"), index=True)
    resumo_criptografico: Mapped[str] = mapped_column(String(64), index=True)
    houve_mudanca: Mapped[bool] = mapped_column(Boolean)
    verificada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ConsultaMeteorologicaModelo(Base):
    __tablename__ = "consultas_meteorologicas"
    identificador: Mapped[int] = mapped_column(primary_key=True)
    execucao_id: Mapped[int] = mapped_column(ForeignKey("execucoes.identificador"), index=True)
    segurado_id: Mapped[int] = mapped_column(ForeignKey("segurados.identificador"), index=True)
    fonte: Mapped[str] = mapped_column(String(80))
    parametros: Mapped[str] = mapped_column(Text)
    resposta: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30))
    tentativa: Mapped[int] = mapped_column(Integer)
    duracao_ms: Mapped[int] = mapped_column(Integer)
    erro: Mapped[str | None] = mapped_column(Text, nullable=True)
    consultada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DecisaoModelo(Base):
    __tablename__ = "decisoes"
    identificador: Mapped[int] = mapped_column(primary_key=True)
    execucao_id: Mapped[int] = mapped_column(ForeignKey("execucoes.identificador"), index=True)
    segurado_id: Mapped[int] = mapped_column(ForeignKey("segurados.identificador"), index=True)
    tipo_evento: Mapped[str | None] = mapped_column(String(40), nullable=True)
    elegivel: Mapped[bool] = mapped_column(Boolean)
    motivo: Mapped[str] = mapped_column(Text)
    decidida_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AuditoriaAgenteModelo(Base):
    __tablename__ = "auditorias_agentes"
    identificador: Mapped[int] = mapped_column(primary_key=True)
    execucao_id: Mapped[int] = mapped_column(ForeignKey("execucoes.identificador"), index=True)
    agente: Mapped[str] = mapped_column(String(60))
    iniciada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    concluida_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duracao_ms: Mapped[int] = mapped_column(Integer)
    entrada_resumo: Mapped[str] = mapped_column(Text)
    saida_resumo: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30))
    erro: Mapped[str | None] = mapped_column(Text, nullable=True)


def criar_fabrica_sessoes(configuracao: Configuracao):
    if configuracao.BANCO_URL.startswith("sqlite:///"):
        caminho = configuracao.BANCO_URL.removeprefix("sqlite:///")
        if caminho != ":memory:":
            Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    motor = create_engine(configuracao.BANCO_URL)
    return sessionmaker(motor, expire_on_commit=False)


def criar_dados_iniciais(fabrica_sessoes) -> None:
    with fabrica_sessoes.begin() as sessao:
        if sessao.query(SeguradoModelo).count():
            return
        sessao.add_all(
            [
                SeguradoModelo(
                    nome="Ana Souza",
                    cidade="São Paulo",
                    estado="SP",
                    pais="BR",
                    latitude=-23.5505,
                    longitude=-46.6333,
                    apolices=[ApoliceModelo(tipo="residencial"), ApoliceModelo(tipo="automovel")],
                ),
                SeguradoModelo(
                    nome="Bruno Lima",
                    cidade="Santos",
                    estado="SP",
                    pais="BR",
                    latitude=-23.9608,
                    longitude=-46.3336,
                    apolices=[ApoliceModelo(tipo="automovel")],
                ),
                SeguradoModelo(
                    nome="Carla Alves",
                    cidade="Campinas",
                    estado="SP",
                    pais="BR",
                    latitude=-22.9056,
                    longitude=-47.0608,
                    apolices=[ApoliceModelo(tipo="residencial")],
                ),
            ]
        )


def listar_segurados(fabrica_sessoes) -> list[Segurado]:
    with fabrica_sessoes() as sessao:
        modelos = (
            sessao.query(SeguradoModelo)
            .where(SeguradoModelo.ativo.is_(True))
            .order_by(SeguradoModelo.nome)
            .all()
        )
        return [
            Segurado(
                m.identificador,
                m.nome,
                m.cidade,
                m.estado,
                m.pais,
                m.latitude,
                m.longitude,
                tuple(TipoApolice(a.tipo) for a in m.apolices),
                m.canal_preferido,
            )
            for m in modelos
        ]


def agora_utc() -> datetime:
    return datetime.now(UTC)
