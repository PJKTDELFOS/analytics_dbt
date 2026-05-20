-- models/marts/mart_por_uf.sql
-- Total de licitações e valor agregado por estado

with intermediate as (

    select * from {{ ref('int_licitacoes_enriquecidas') }}

),

agregado as (

    select
        uf,
        uf_nome,
        regiao,
        count(*)                                        as total_licitacoes,
        count(*) filter (where is_ativa)                as total_ativas,
        count(*) filter (where is_alto_valor)           as total_alto_valor,
        round(sum(valor_total_estimado), 2)             as valor_total,
        round(avg(valor_total_estimado), 2)             as valor_medio,
        round(max(valor_total_estimado), 2)             as valor_maximo,
        count(distinct orgao_cnpj)                      as total_orgaos

    from intermediate

    group by uf, uf_nome, regiao

)

select
    *,
    round(total_ativas * 100.0 / nullif(total_licitacoes, 0), 1) as pct_ativas
from agregado
order by total_licitacoes desc