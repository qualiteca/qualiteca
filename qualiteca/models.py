from sqlalchemy.orm import sessionmaker, Session, declarative_base, relationship
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    DateTime,
    String, LargeBinary, ForeignKey, Date, func)
from typing import Any
import pendulum, pytz
import hashlib

engine = create_engine('sqlite:///biblioteca.db')
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

def agora():
    return pendulum.now(pytz.UTC)


class ModeloBase(Base):

    __abstract__ = True

    id = Column(Integer, primary_key=True)
    registrado_em = Column(DateTime, default=agora, nullable=False)
    editado_em = Column(DateTime)
    excluido_em = Column(DateTime)

    @classmethod
    @property
    def excluidos(cls):
        return cls.excluido_em.is_not(None)

    @property
    def excluido(self):
        return self.excluido_em is not None

    @classmethod
    @property
    def editados(cls):
        return cls.editado_em.is_not(None)

    @property
    def editado(self):
        return self.editado_em is not None

    # def __eq__(self, other):
    #     return all(
    #         [
    #             self.__class__ == other.__class__,
    #             self.id == other.id
    #         ]
    #     )

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        parametros = ', '.join(f'{k}={repr(v)}' for k, v in vars(self).items())
        return f"{self.__class__.__name__}({parametros})"

    def __str__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"

    @classmethod
    def adicionar(cls, **kwargs):
        try:
            novo = cls(**kwargs)
            session.add(novo)
            session.commit()
            return novo
        except Exception as e:
            session.rollback()
            raise e

    @classmethod
    def retornar(cls, campo='id', valor=None):
        if valor is None:
            filtro = True
        else:
            filtro = (getattr(cls, campo) == valor)
        return session.query(cls).where(cls.excluidos == False, filtro).all()


    def editar(self, edicao: dict[str, Any]):
        for campo_edicao, valor_edicao in edicao.items():
            setattr(self, campo_edicao, valor_edicao)

        setattr(self, 'editado_em', agora())

        try:
            session.commit()

        except Exception as e:
            session.rollback()
            raise e
        
        finally:
            return self


    @classmethod
    def editar_muitos(cls, edicao: dict[str, Any], campo='id', valor=None):
        objetos = cls.retornar(campo=campo, valor=valor)
        editados = []
        for objeto in objetos:
            editados.append(objeto.editar(edicao=edicao))
        return editados
    

    def excluir(self):
        return self.editar(edicao={'excluido_em':agora()})

    
    @classmethod
    def excluir_muitos(cls, campo='id', valor=None):
        return cls.editar_muitos(
            campo=campo,
            valor=valor,
            edicao={
                'excluido_em': agora(),
            }
        )


class Usuario(ModeloBase):
    __tablename__ = 'usuarios'

    nome = Column(String, nullable=False)
    email = Column(String, nullable=False)
    genero_preferidos = Column(String, nullable=True)

    emprestimos = relationship('Emprestimo', back_populates='leitor')
    doacao = relationship('Livro', back_populates='doador')

    def volume_emprestimos_ativos(self):

        livros_emprestados = session.query(Emprestimo.id).filter(
            (Emprestimo.devolvidos == False), (self.id == Emprestimo.leitor_id)
        ).count()

        return livros_emprestados


    def emprestimos_pendentes(self):
        return Emprestimo.retornar_por_leitor(leitor=self, devolvidos=False)


    def __str__(self):
        return f"({self.id}) {self.nome}"


    @property
    def chave_container(self):
        letras_correspondentes = {
            '0': 'ab',
            '1': 'cd',
            '2': 'ef',
            '3': 'gh',
            '4': 'ij',
            '5': 'kl',
            '6': 'mn',
            '7': 'op',
            '8': 'qr',
            '9': 'st'
        }

        dados_para_hash = f"{self.id}{self.nome}{self.email}{self.genero_preferidos}{self.registrado_em}"
        sha256_hash = hashlib.sha256(dados_para_hash.encode()).hexdigest()

        retorno = ''
        for caractere in sha256_hash:
            if caractere in letras_correspondentes.keys():
                retorno += letras_correspondentes[caractere]
            else:
                retorno += caractere

        return retorno


class Livro(ModeloBase):
    __tablename__ = 'livros'
    def tempo_emprestimo_padrao(): return 1

    titulo = Column(String, nullable=False)
    autor = Column(String, nullable=False)
    genero = Column(String, nullable=False)
    doador_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    foto_livro = Column(LargeBinary, nullable=False)
    observacao = Column(String, nullable=True)
    extensao_foto = Column(String, nullable=False)

    doador = relationship('Usuario', back_populates='doacao')
    emprestimos = relationship('Emprestimo', back_populates='livro')


    def emprestimos_pendentes(self):
        return Emprestimo.retornar_por_livro(livro=self, devolvidos=False)

    @classmethod
    def disponiveis(cls):
        livros_emprestados = (
            session.query(Emprestimo.livro_id)
            .filter( ~Emprestimo.devolvidos)
        )

        return session.query(Livro).filter(
            Livro.id.not_in(livros_emprestados)
        ).all()



    def __str__(self):
        return f"({self.id}) {self.titulo} ({self.autor})"


class Emprestimo(ModeloBase):
    __tablename__ = 'emprestimos'

    leitor_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    livro_id = Column(Integer, ForeignKey('livros.id'), nullable=False)
    
    emprestado_em = Column(Date, nullable=False, default=agora)
    devolucao_em = Column(Date, nullable=False, default=agora)
    devolvido_em = Column(Date)
    vezes_adiado = Column(Integer, default=int)

    leitor = relationship('Usuario', back_populates='emprestimos')
    livro = relationship('Livro', back_populates='emprestimos')

    @property
    def devolvido(self):
        return self.devolvido_em is not None
    
    @classmethod
    @property
    def devolvidos(cls):
        return cls.devolvido_em.is_not(None)
    
    @property
    def dias_para_termino(self):
        date_temp = pendulum.datetime(self.devolucao_em.year, self.devolucao_em.month, self.devolucao_em.day, 0, 0, 0)
        return date_temp.date().diff(agora().date()).in_days()

    @classmethod
    @property
    def dias_para_terminos(cls):
        return func.datediff(func.now(), cls.devolucao_em).label('dias_para_terminos')


    def devolver(self):
        return self.editar({
            'devolvido_em' :  agora().date()
        })


    def mais_prazo(self, aumento_prazo: int = 1):
        date_temp = pendulum.datetime(self.devolucao_em.year, self.devolucao_em.month, self.devolucao_em.day, 0, 0, 0)
        return  self.editar({
            'devolucao_em' :  date_temp.add(days=aumento_prazo).date(),
            'vezes_adiado' : self.vezes_adiado + 1
        })


    @classmethod
    def retornar_por_leitor(cls, leitor:Usuario, devolvidos:bool = False):
        return session.query(cls).where(cls.leitor == leitor, cls.devolvidos == devolvidos).all()


    @classmethod
    def retornar_por_livro(cls, livro:Livro, devolvidos:bool = False):
        return session.query(cls).where(cls.livro == livro, cls.devolvidos == devolvidos).all()

    @classmethod
    def retornar_abertos_ordenados(cls, session: Session = session):

        emprestimos_abertos = cls.retornar(
            campo='devolvidos',
            valor=False
        )
        if emprestimos_abertos:
            return sorted(emprestimos_abertos, key=lambda x: x.devolucao_em)
        else:
            return []

    def __str__(self):
        return f'{self.livro.titulo} para {self.leitor.nome} até {self.devolucao_em.strftime("%A, %d de %B de %Y")}'




Base.metadata.create_all(engine)