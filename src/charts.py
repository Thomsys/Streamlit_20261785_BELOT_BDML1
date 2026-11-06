# Small helpers to give the same look to every chart (same idea as style_bokeh in my Uber dashboard)
import streamlit as st

TEXTE = '#1c2333'
GRILLE = '#e1e6ef'
TEXTE_SECONDAIRE = '#52607a'


def style_plotly(fig, hauteur=380, legende=True):
    # Light grid, no frame, legend on top, same fonts as the page
    fig.update_layout(height=hauteur, margin=dict(t=85, b=10, l=10, r=10), plot_bgcolor='white',
                      paper_bgcolor='white', font=dict(color=TEXTE_SECONDAIRE),
                      title_font=dict(color=TEXTE, size=15), title_y=0.97, title_yanchor='top', showlegend=legende,
                      legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0, title=None),
                      hoverlabel=dict(bgcolor='white'))
    fig.update_xaxes(showgrid=False, linecolor=GRILLE)
    fig.update_yaxes(gridcolor=GRILLE, zeroline=False)
    return fig


def afficher_plotly(fig, cle=None):
    # Every chart in a card (container with border), like in my portfolio
    with st.container(border=True):
        st.plotly_chart(fig, width='stretch', key=cle)


def afficher_altair(chart):
    with st.container(border=True):
        st.altair_chart(chart, width='stretch')


def question(texte):
    # Each analysis starts with the business question it answers
    st.markdown(f'**:material/help: Question :** {texte}')


def lecture(observation, interpretation):
    # Observation (what the data shows) / Interpretation (what it means) like in my notebooks
    st.caption(f'**Observation :** {observation}')
    st.caption(f'**Interprétation :** {interpretation}')
