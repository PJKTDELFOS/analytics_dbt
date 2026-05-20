-- models/intermediate/int_licitacoes_enriquecidas.sql
-- Camada intermediate: regras de negócio e enriquecimento
-- Consome a staging e prepara os dados para os marts

with staging as (

    select * from {{ ref('st_licitacoes') }}

),

enriquecida as (

    select
        *,

        -- Classificação de valor
        case
            when valor_total_estimado = 0.0        then 'Não informado'
            when valor_total_estimado < 10000       then 'Até R$ 10k'
            when valor_total_estimado < 50000       then 'R$ 10k – R$ 50k'
            when valor_total_estimado < 100000      then 'R$ 50k – R$ 100k'
            when valor_total_estimado < 500000      then 'R$ 100k – R$ 500k'
            when valor_total_estimado < 1000000     then 'R$ 500k – R$ 1M'
            else                                         'Acima de R$ 1M'
        end                                         as faixa_valor,

        -- Flag de licitação ativa
        case
            when data_encerramento >= current_date  then true
            else                                         false
        end                                         as is_ativa,

        -- Flag de alto valor (acima de R$ 100k)
        case
            when valor_total_estimado >= 100000     then true
            else                                         false
        end                                         as is_alto_valor,

        -- Dias até encerramento
        case
            when data_encerramento >= current_date
            then datediff('day', current_date, data_encerramento::date)
            else null
        end                                         as dias_para_encerramento,

        -- Dias desde publicação
        datediff('day', data_publicacao_pncp::date, current_date) as dias_desde_publicacao,

        -- Região do Brasil
        case uf
            when 'AC' then 'Norte'
            when 'AM' then 'Norte'
            when 'AP' then 'Norte'
            when 'PA' then 'Norte'
            when 'RO' then 'Norte'
            when 'RR' then 'Norte'
            when 'TO' then 'Norte'
            when 'AL' then 'Nordeste'
            when 'BA' then 'Nordeste'
            when 'CE' then 'Nordeste'
            when 'MA' then 'Nordeste'
            when 'PB' then 'Nordeste'
            when 'PE' then 'Nordeste'
            when 'PI' then 'Nordeste'
            when 'RN' then 'Nordeste'
            when 'SE' then 'Nordeste'
            when 'DF' then 'Centro-Oeste'
            when 'GO' then 'Centro-Oeste'
            when 'MS' then 'Centro-Oeste'
            when 'MT' then 'Centro-Oeste'
            when 'ES' then 'Sudeste'
            when 'MG' then 'Sudeste'
            when 'RJ' then 'Sudeste'
            when 'SP' then 'Sudeste'
            when 'PR' then 'Sul'
            when 'RS' then 'Sul'
            when 'SC' then 'Sul'
            else           'Não informado'
        end                                         as regiao

    from staging

)

select * from enriquecida