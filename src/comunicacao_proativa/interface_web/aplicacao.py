import secrets
from hmac import compare_digest

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from sqlalchemy import delete, func, select
from sqlalchemy.orm import selectinload

from comunicacao_proativa.aplicacao.executor import executar_fluxo
from comunicacao_proativa.configuracao import obter_configuracao
from comunicacao_proativa.infraestrutura.banco_dados import (
    ApoliceModelo,
    AuditoriaAgenteModelo,
    ConsultaMeteorologicaModelo,
    DecisaoModelo,
    EventoModelo,
    ExecucaoModelo,
    MensagemModelo,
    NotificacaoModelo,
    SeguradoModelo,
    VerificacaoMeteorologicaModelo,
    criar_fabrica_sessoes,
)
from comunicacao_proativa.infraestrutura.geocodificacao import (
    ESTADOS,
    CidadeNaoEncontrada,
    GeocodificadorOpenMeteo,
)
from comunicacao_proativa.infraestrutura.modelos_linguagem import normalizar_mensagem

from .formatacao import formatar_data_hora_brasilia


def criar_aplicacao(configuracao=None) -> Flask:
    configuracao = configuracao or obter_configuracao()
    aplicacao = Flask(__name__, template_folder="templates", static_folder="estaticos")
    aplicacao.secret_key = configuracao.CHAVE_SECRETA
    fabrica_sessoes = criar_fabrica_sessoes(configuracao)
    aplicacao.extensions["fabrica_sessoes"] = fabrica_sessoes
    aplicacao.extensions["configuracao_proativa"] = configuracao
    aplicacao.extensions["geocodificador"] = GeocodificadorOpenMeteo()

    @aplicacao.before_request
    def proteger_formularios():
        token = session.setdefault("token_csrf", secrets.token_urlsafe(32))
        if configuracao.CSRF_ATIVO and request.method == "POST":
            recebido = request.form.get("_csrf_token", "")
            if not recebido or not compare_digest(token, recebido):
                abort(400, "Token CSRF ausente ou inválido.")

    @aplicacao.context_processor
    def disponibilizar_token_csrf():
        return {"token_csrf": session.get("token_csrf", "")}

    rotulos = {
        "automovel": "automóvel",
        "automatica": "automática",
        "concluida": "concluída",
        "concluida_com_ressalvas": "concluída com ressalvas",
        "contingencia": "contingência",
        "chuva_intensa": "chuva intensa",
        "vento_forte": "vento forte",
    }

    @aplicacao.template_filter("rotulo")
    def rotulo(valor):
        return rotulos.get(str(valor), str(valor).replace("_", " "))

    aplicacao.add_template_filter(normalizar_mensagem, "normalizar_mensagem")
    aplicacao.add_template_filter(formatar_data_hora_brasilia, "data_hora_brasilia")

    @aplicacao.get("/")
    def painel():
        with fabrica_sessoes() as sessao:
            totais = {
                "segurados": sessao.scalar(
                    select(func.count())
                    .select_from(SeguradoModelo)
                    .where(SeguradoModelo.ativo.is_(True))
                ),
                "execuções": sessao.scalar(select(func.count()).select_from(ExecucaoModelo)),
                "eventos": sessao.scalar(select(func.count()).select_from(EventoModelo)),
                "notificações": sessao.scalar(select(func.count()).select_from(NotificacaoModelo)),
            }
            total_eventos = (
                select(func.count(EventoModelo.identificador))
                .where(EventoModelo.execucao_id == ExecucaoModelo.identificador)
                .correlate(ExecucaoModelo)
                .scalar_subquery()
            )
            total_notificacoes = (
                select(func.count(NotificacaoModelo.identificador))
                .where(NotificacaoModelo.execucao_id == ExecucaoModelo.identificador)
                .correlate(ExecucaoModelo)
                .scalar_subquery()
            )
            execucoes = sessao.execute(
                select(ExecucaoModelo, total_eventos, total_notificacoes)
                .order_by(ExecucaoModelo.identificador.desc())
                .limit(8)
            ).all()
        return render_template(
            "painel.html",
            totais=totais,
            execucoes=execucoes,
        )

    @aplicacao.post("/execucoes/excluir-todas")
    def excluir_todas_execucoes():
        with fabrica_sessoes.begin() as sessao:
            em_execucao = sessao.scalar(
                select(func.count())
                .select_from(ExecucaoModelo)
                .where(ExecucaoModelo.status == "executando")
            )
            if em_execucao:
                flash(
                    "Há uma verificação em andamento. Aguarde a conclusão antes de "
                    "excluir o histórico.",
                    "erro",
                )
                return redirect(url_for("painel"))

            total = sessao.scalar(select(func.count()).select_from(ExecucaoModelo))
            sessao.execute(delete(NotificacaoModelo))
            sessao.execute(delete(MensagemModelo))
            sessao.execute(delete(EventoModelo))
            sessao.execute(delete(ConsultaMeteorologicaModelo))
            sessao.execute(delete(DecisaoModelo))
            sessao.execute(delete(AuditoriaAgenteModelo))
            sessao.execute(delete(VerificacaoMeteorologicaModelo))
            sessao.execute(delete(ExecucaoModelo))

        if total:
            flash(
                f"{total} execução(ões) e todo o histórico relacionado foram excluídos.", "sucesso"
            )
        else:
            flash("Não havia execuções para excluir.", "sucesso")
        return redirect(url_for("painel"))

    @aplicacao.get("/segurados")
    def segurados():
        with fabrica_sessoes() as sessao:
            itens = sessao.scalars(
                select(SeguradoModelo)
                .options(selectinload(SeguradoModelo.apolices))
                .where(SeguradoModelo.ativo.is_(True))
                .order_by(SeguradoModelo.nome)
            ).all()
        return render_template("segurados.html", segurados=itens)

    @aplicacao.route("/segurados/novo", methods=["GET", "POST"])
    def novo_segurado():
        if request.method == "GET":
            return render_template(
                "novo_segurado.html",
                estados=ESTADOS,
                titulo="Novo segurado",
                rotulo="CADASTRO",
                texto_botao="Localizar cidade e cadastrar",
                apolices_selecionadas=[],
            )

        nome = request.form.get("nome", "").strip()
        cidade = request.form.get("cidade", "").strip()
        estado = request.form.get("estado", "").strip().upper()
        tipos_apolice = request.form.getlist("apolices")
        canal_preferido = request.form.get("canal_preferido", "push")
        tipos_validos = {"residencial", "automovel"}
        canais_validos = {"push", "sms", "email"}
        if len(nome) < 3:
            flash("Informe um nome com pelo menos três caracteres.", "erro")
        elif len(cidade) < 2:
            flash("Informe o nome da cidade.", "erro")
        elif estado not in ESTADOS:
            flash("Selecione uma UF válida.", "erro")
        elif not tipos_apolice or any(item not in tipos_validos for item in tipos_apolice):
            flash("Selecione pelo menos uma apólice válida.", "erro")
        elif canal_preferido not in canais_validos:
            flash("Selecione um canal de comunicação válido.", "erro")
        else:
            try:
                localizacao = aplicacao.extensions["geocodificador"].buscar(cidade, estado)
                with fabrica_sessoes.begin() as sessao:
                    sessao.add(
                        SeguradoModelo(
                            nome=nome,
                            cidade=localizacao.cidade,
                            estado=localizacao.estado,
                            pais=localizacao.pais,
                            latitude=localizacao.latitude,
                            longitude=localizacao.longitude,
                            canal_preferido=canal_preferido,
                            apolices=[ApoliceModelo(tipo=item) for item in tipos_apolice],
                        )
                    )
                flash(
                    f"Segurado cadastrado em {localizacao.cidade}/{localizacao.estado}.",
                    "sucesso",
                )
                return redirect(url_for("segurados"))
            except CidadeNaoEncontrada as erro:
                flash(str(erro), "erro")
            except Exception as erro:
                flash(f"Não foi possível consultar a cidade: {erro}", "erro")
        return render_template(
            "novo_segurado.html",
            estados=ESTADOS,
            titulo="Novo segurado",
            rotulo="CADASTRO",
            texto_botao="Localizar cidade e cadastrar",
            apolices_selecionadas=tipos_apolice,
        ), 400

    @aplicacao.route("/segurados/<int:identificador>/editar", methods=["GET", "POST"])
    def editar_segurado(identificador: int):
        with fabrica_sessoes() as sessao:
            segurado = sessao.scalar(
                select(SeguradoModelo)
                .options(selectinload(SeguradoModelo.apolices))
                .where(
                    SeguradoModelo.identificador == identificador,
                    SeguradoModelo.ativo.is_(True),
                )
            )
            if segurado is None:
                return "Segurado não encontrado", 404
            dados_atuais = {
                "nome": segurado.nome,
                "cidade": segurado.cidade,
                "estado": segurado.estado,
                "canal_preferido": segurado.canal_preferido,
            }
            apolices_atuais = [apolice.tipo for apolice in segurado.apolices]

        if request.method == "GET":
            return render_template(
                "novo_segurado.html",
                estados=ESTADOS,
                titulo="Editar segurado",
                rotulo="EDIÇÃO",
                texto_botao="Salvar alterações",
                dados=dados_atuais,
                apolices_selecionadas=apolices_atuais,
            )

        nome = request.form.get("nome", "").strip()
        cidade = request.form.get("cidade", "").strip()
        estado = request.form.get("estado", "").strip().upper()
        tipos_apolice = request.form.getlist("apolices")
        canal_preferido = request.form.get("canal_preferido", "push")
        tipos_validos = {"residencial", "automovel"}
        canais_validos = {"push", "sms", "email"}
        if len(nome) < 3:
            flash("Informe um nome com pelo menos três caracteres.", "erro")
        elif len(cidade) < 2:
            flash("Informe o nome da cidade.", "erro")
        elif estado not in ESTADOS:
            flash("Selecione uma UF válida.", "erro")
        elif not tipos_apolice or any(item not in tipos_validos for item in tipos_apolice):
            flash("Selecione pelo menos uma apólice válida.", "erro")
        elif canal_preferido not in canais_validos:
            flash("Selecione um canal de comunicação válido.", "erro")
        else:
            try:
                localizacao = None
                if (
                    cidade.casefold() != dados_atuais["cidade"].casefold()
                    or estado != dados_atuais["estado"]
                ):
                    localizacao = aplicacao.extensions["geocodificador"].buscar(cidade, estado)
                with fabrica_sessoes.begin() as sessao:
                    segurado = sessao.scalar(
                        select(SeguradoModelo)
                        .options(selectinload(SeguradoModelo.apolices))
                        .where(
                            SeguradoModelo.identificador == identificador,
                            SeguradoModelo.ativo.is_(True),
                        )
                    )
                    if segurado is None:
                        return "Segurado não encontrado", 404
                    segurado.nome = nome
                    segurado.canal_preferido = canal_preferido
                    if localizacao is not None:
                        segurado.cidade = localizacao.cidade
                        segurado.estado = localizacao.estado
                        segurado.pais = localizacao.pais
                        segurado.latitude = localizacao.latitude
                        segurado.longitude = localizacao.longitude
                    segurado.apolices.clear()
                    segurado.apolices.extend(ApoliceModelo(tipo=item) for item in tipos_apolice)
                flash(f"Dados de {nome} atualizados com sucesso.", "sucesso")
                return redirect(url_for("segurados"))
            except CidadeNaoEncontrada as erro:
                flash(str(erro), "erro")
            except Exception as erro:
                flash(f"Não foi possível atualizar o segurado: {erro}", "erro")

        return render_template(
            "novo_segurado.html",
            estados=ESTADOS,
            titulo="Editar segurado",
            rotulo="EDIÇÃO",
            texto_botao="Salvar alterações",
            dados=dados_atuais,
            apolices_selecionadas=tipos_apolice,
        ), 400

    @aplicacao.post("/segurados/<int:identificador>/excluir")
    def excluir_segurado(identificador: int):
        with fabrica_sessoes.begin() as sessao:
            segurado = sessao.get(SeguradoModelo, identificador)
            if segurado is None or not segurado.ativo:
                flash("Segurado não encontrado ou já excluído.", "erro")
            else:
                segurado.ativo = False
                flash(
                    f"{segurado.nome} foi excluído das próximas análises. "
                    "O histórico foi preservado.",
                    "sucesso",
                )
        return redirect(url_for("segurados"))

    @aplicacao.post("/executar")
    def executar():
        try:
            identificador = executar_fluxo(configuracao, fabrica_sessoes, origem="manual")
            flash(f"Execução #{identificador} finalizada.", "sucesso")
            return redirect(url_for("detalhe_execucao", identificador=identificador))
        except Exception as erro:
            flash(f"Não foi possível concluir o fluxo: {erro}", "erro")
            return redirect(url_for("painel"))

    @aplicacao.get("/execucoes/<int:identificador>")
    def detalhe_execucao(identificador: int):
        with fabrica_sessoes() as sessao:
            execucao = sessao.get(ExecucaoModelo, identificador)
            if execucao is None:
                return "Execução não encontrada", 404
            eventos = sessao.scalars(
                select(EventoModelo).where(EventoModelo.execucao_id == identificador)
            ).all()
            notificacoes = sessao.execute(
                select(NotificacaoModelo, SeguradoModelo.nome)
                .join(SeguradoModelo, SeguradoModelo.identificador == NotificacaoModelo.segurado_id)
                .where(NotificacaoModelo.execucao_id == identificador)
            ).all()
            auditorias = sessao.scalars(
                select(AuditoriaAgenteModelo)
                .where(AuditoriaAgenteModelo.execucao_id == identificador)
                .order_by(AuditoriaAgenteModelo.identificador)
            ).all()
            decisoes = sessao.execute(
                select(DecisaoModelo, SeguradoModelo.nome)
                .join(SeguradoModelo, SeguradoModelo.identificador == DecisaoModelo.segurado_id)
                .where(DecisaoModelo.execucao_id == identificador)
                .order_by(DecisaoModelo.identificador)
            ).all()
            consultas = sessao.scalars(
                select(ConsultaMeteorologicaModelo)
                .where(ConsultaMeteorologicaModelo.execucao_id == identificador)
                .order_by(ConsultaMeteorologicaModelo.identificador)
            ).all()
        return render_template(
            "execucao.html",
            execucao=execucao,
            eventos=eventos,
            notificacoes=notificacoes,
            auditorias=auditorias,
            decisoes=decisoes,
            consultas=consultas,
        )

    return aplicacao
