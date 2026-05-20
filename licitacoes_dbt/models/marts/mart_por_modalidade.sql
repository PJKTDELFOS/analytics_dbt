-- models/marts/mart_por_modalidade.sql
-- Distribuição por modalidade de licitação

with intermediate as (

    select * from {{ ref('int_licitacoes_enriquecidas') }}

),

agregado as (

    select
        modalidade_id,
        modalidade_nome,
        count(*)                                        as total_licitacoes,
        count(*) filter (where is_ativa)                as total_ativas,
        count(*) filter (where is_alto_valor)           as total_alto_valor,
        round(sum(valor_total_estimado), 2)             as valor_total,
        round(avg(valor_total_estimado), 2)             as valor_medio,
        count(distinct uf)                              as total_ufs,
        count(distinct orgao_cnpj)                      as total_orgaos

    from intermediate

    group by modalidade_id, modalidade_nome

)

select
    *,
    round(total_licitacoes * 100.0 / sum(total_licitacoes) over (), 2) as pct_do_total
from agregado
order by total_licitacoes desc