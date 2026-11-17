FIELDS = {
    'Pavimentação': ['Asfáltica', 'Paralelepípedo', 'Intertravado', 'Concreto', 'Terra / sem pavimentação', 'Outra', 'Não verificado'],
    'Abastecimento de água': ['Rede pública', 'Poço / solução individual', 'Outra solução', 'Não disponível', 'Não verificado'],
    'Saneamento / drenagem': ['Rede / sistema existente', 'Solução individual', 'Não disponível', 'Não verificado'],
    'Esgotamento sanitário': ['Rede coletora', 'Fossa / solução individual', 'Não disponível', 'Não verificado'],
    'Energia elétrica': ['Ligação / rede disponível', 'Solução individual', 'Não disponível', 'Não verificado'],
    'Telefonia': ['Rede / serviço disponível', 'Não disponível', 'Não verificado'],
}

def build_infrastructure_considerando(data, source):
    if not source.strip():
        raise ValueError('Informe a fonte de verificação da infraestrutura (vistoria, documento, declaração etc.).')
    segments = []
    for area, label in [('logradouro', 'no logradouro'), ('imovel', 'no imóvel avaliando')]:
        parts=[]
        for field, _ in FIELDS.items():
            val = data.get(area, {}).get(field, 'Não verificado')
            if val != 'Não verificado':
                parts.append(f'{field.lower()}: {val.lower()}')
        if parts:
            segments.append(f'{label}, foram informadas as seguintes condições: ' + '; '.join(parts))
    if not segments:
        return ''
    return ('Considerando que ' + '; e que '.join(segments) +
            f', conforme {source.strip()}, informações sujeitas à confirmação quanto à disponibilidade, regularidade e efetivo atendimento;')
