-- models/marts/mart_por_orgao.sql
-- Top órgãos por volume de licitações

with intermediate as (

    select * from {{ ref('int_licitacoes_enriquecidas') }}

),

agregado as (

    select
        orgao_cnpj,
        orgao_razao_social,
        orgao_esfera,
        orgao_poder,
        uf,
        municipio,
        regiao,
        count(*)                                        as total_licitacoes,
        count(*) filter (where is_ativa)                as total_ativas,
        count(*) filter (where is_alto_valor)           as total_alto_valor,
        round(sum(valor_total_estimado), 2)             as valor_total,
        round(avg(valor_total_estimado), 2)             as valor_medio,
        min(data_publicacao_pncp)                       as primeira_publicacao,
        max(data_publicacao_pncp)                       as ultima_publicacao

    from intermediate

    group by
        orgao_cnpj,
        orgao_razao_social,
        orgao_esfera,
        orgao_poder,
        uf,
        municipio,
        regiao

)

select
    *,
    round(total_ativas * 100.0 / nullif(total_licitacoes, 0), 1) as pct_ativas
from agregado
order by total_licitacoes desc