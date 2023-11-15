import streamlit as st


class Home:
    nome = 'Home'

    def __init__(self) -> None:
        super().__init__()
        st.header('Qualiteca', anchor=False, divider='orange')
        st.markdown(
            'Biblioteca formada com doações de livros'
        )
