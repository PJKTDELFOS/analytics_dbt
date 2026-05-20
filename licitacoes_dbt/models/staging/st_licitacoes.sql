-- models/staging/st_licitacoes.sql
-- Camada staging: limpeza 1:1 da tabela bruta
-- Uma linha de transformação por coluna — sem regras de negócio aqui

with source as (

    select * from raw_licitacoes

),

staged as (

    select
        -- Identificadores
        id                                              as licitacao_id,
        numero_controle_pncp,
        identificador_certame,

        -- Localização
        upper(trim(uf))                                 as uf,
        uf_nome,
        municipio,

        -- Órgão
        orgao_cnpj,
        upper(trim(orgao_razao_social))                 as orgao_razao_social,
        case orgao_esfera
            when 'E' then 'Estadual'
            when 'F' then 'Federal'
            when 'M' then 'Municipal'
            else 'Não informado'
        end                                             as orgao_esfera,
        case orgao_poder
            when 'E' then 'Executivo'
            when 'L' then 'Legislativo'
            when 'J' then 'Judiciário'
            else 'Não informado'
        end                                             as orgao_poder,

        -- Modalidade e situação
        modalidade_id,
        modalidade_nome,
        situacao_compra_nome,

        -- Objeto
        trim(objeto)                                    as objeto,
        trim(objeto_compra)                             as objeto_compra,

        -- Valores
        coalesce(valor_total_estimado, 0.0)             as valor_total_estimado,
        coalesce(valor_total_homologado, 0.0)           as valor_total_homologado,

        -- Flags
        coalesce(srp, false)                            as is_srp,

        -- Detalhes
        modo_disputa_nome,
        processo,
        numero_compra,
        ano_compra,
        trim(amparo_legal_nome)                         as amparo_legal_nome,
        link_sistema_origem,

        -- Datas
        data_publicacao_pncp::timestamp                 as data_publicacao_pncp,
        data_abertura_proposta::timestamp               as data_abertura_proposta,
        data_encerramento::timestamp                    as data_encerramento,
        data_coleta::timestamp                          as data_coleta,

        -- Datas derivadas úteis
        year(data_publicacao_pncp)                      as ano_publicacao,
        month(data_publicacao_pncp)                     as mes_publicacao,
        year(data_encerramento)                         as ano_encerramento,
        month(data_encerramento)                        as mes_encerramento

    from source

)

select * from staged