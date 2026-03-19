--
-- PostgreSQL database dump
--

-- Dumped from database version 12.10
-- Dumped by pg_dump version 15.0

-- Started on 2022-12-24 17:58:03

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 8 (class 2615 OID 647168)
-- Name: ab; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA ab;


ALTER SCHEMA ab OWNER TO postgres;

--
-- TOC entry 6 (class 2615 OID 2200)
-- Name: public; Type: SCHEMA; Schema: -; Owner: postgres
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO postgres;

--
-- TOC entry 208 (class 1255 OID 663914)
-- Name: isvalueallowed(integer); Type: FUNCTION; Schema: ab; Owner: postgres
--

CREATE FUNCTION ab.isvalueallowed(idregistro integer) RETURNS bit
    LANGUAGE plpgsql
    AS $$ begin
	
		IF (SELECT COUNT(*) FROM ab."Personas" WHERE registro = idRegistro) =8 then RETURN 0;
		ELSE RETURN 1;
		END IF;
	
	end;
	$$;


ALTER FUNCTION ab.isvalueallowed(idregistro integer) OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 207 (class 1259 OID 663599)
-- Name: DatosPersonales; Type: TABLE; Schema: ab; Owner: postgres
--

CREATE TABLE ab."DatosPersonales" (
    registro bigint NOT NULL,
    nombre character varying,
    apellido1 character varying,
    apellido2 character varying,
    lugarsacramento character varying,
    oficiante character varying,
    profesion character varying,
    profesionpadre character varying,
    fechanacimiento character varying,
    fechasacramento character varying,
    residencia character varying,
    lugarinscripcion character varying,
    notas character varying
);


ALTER TABLE ab."DatosPersonales" OWNER TO postgres;

--
-- TOC entry 206 (class 1259 OID 663554)
-- Name: Personas; Type: TABLE; Schema: ab; Owner: postgres
--

CREATE TABLE ab."Personas" (
    "ID" bigint NOT NULL,
    registro integer,
    relacion character varying,
    nombre character varying,
    apellido1 character varying,
    apellido2 character varying,
    lugarnacimiento character varying,
    CONSTRAINT max8registros CHECK ((ab.isvalueallowed(registro) = '1'::"bit"))
);


ALTER TABLE ab."Personas" OWNER TO postgres;

--
-- TOC entry 205 (class 1259 OID 663552)
-- Name: Personas_ID_seq; Type: SEQUENCE; Schema: ab; Owner: postgres
--

CREATE SEQUENCE ab."Personas_ID_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE ab."Personas_ID_seq" OWNER TO postgres;

--
-- TOC entry 2855 (class 0 OID 0)
-- Dependencies: 205
-- Name: Personas_ID_seq; Type: SEQUENCE OWNED BY; Schema: ab; Owner: postgres
--

ALTER SEQUENCE ab."Personas_ID_seq" OWNED BY ab."Personas"."ID";


--
-- TOC entry 203 (class 1259 OID 655360)
-- Name: Registros; Type: TABLE; Schema: ab; Owner: postgres
--

CREATE TABLE ab."Registros" (
    "Registro" bigint NOT NULL,
    "Sacramentos" integer,
    "Libro" character varying(50),
    "Folio" character varying(20),
    "Asiento" character varying(20),
    "Sexo" "char",
    "Subcon" integer
);


ALTER TABLE ab."Registros" OWNER TO postgres;

--
-- TOC entry 204 (class 1259 OID 655377)
-- Name: Sacramentos; Type: TABLE; Schema: ab; Owner: postgres
--

CREATE TABLE ab."Sacramentos" (
    id integer NOT NULL,
    "Sacramentos" character varying(30)
);


ALTER TABLE ab."Sacramentos" OWNER TO postgres;

--
-- TOC entry 2703 (class 2604 OID 663557)
-- Name: Personas ID; Type: DEFAULT; Schema: ab; Owner: postgres
--

ALTER TABLE ONLY ab."Personas" ALTER COLUMN "ID" SET DEFAULT nextval('ab."Personas_ID_seq"'::regclass);


--
-- TOC entry 2848 (class 0 OID 663599)
-- Dependencies: 207
-- Data for Name: DatosPersonales; Type: TABLE DATA; Schema: ab; Owner: postgres
--

COPY ab."DatosPersonales" (registro, nombre, apellido1, apellido2, lugarsacramento, oficiante, profesion, profesionpadre, fechanacimiento, fechasacramento, residencia, lugarinscripcion, notas) FROM stdin;
675381	Josefa	Casells	nan	Valencia: San Esteban Protomártir	nan	nan	nan	nn - nn - nnnn	17 - 03 - 1761	nan	Valencia: San Esteban Protomártir	...Vda de José Martí
675434	José	Guitarte	nan	Valencia: San Esteban Protomártir	nan	nan	nan	nn - nn - nnnn	17 - 03 - 1761	nan	Valencia: San Esteban Protomártir	...Vdo de Anastasia Insa
96356	Joaquín	Guitarte	Alegre	Valencia: San Esteban Protomártir	nan	nan	nan	nn - nn - nnnn	25 - 02 - 1824	nan	Valencia: San Esteban Protomártir	...
96405	Rosa	Saborit	Arquer	Valencia: San Esteban Protomártir	nan	nan	nan	nn - nn - nnnn	25 - 02 - 1824	nan	Valencia: San Esteban Protomártir	...
21981	Esteban	Guitarte	Gomis	Valencia: San Esteban Protomártir	Fuertes, Lorenzo -	nan	nan	10 - 09 - 1860	12 - 09 - 1860	nan	Valencia: San Esteban Protomártir	...Extendida por orden superior
-- [DATA SKIPPED FOR ab: 2177498 lines approx]
\.


--
-- TOC entry 2847 (class 0 OID 663554)
-- Dependencies: 206
-- Data for Name: Personas; Type: TABLE DATA; Schema: ab; Owner: postgres
--

COPY ab."Personas" ("ID", registro, relacion, nombre, apellido1, apellido2, lugarnacimiento) FROM stdin;
578	675381	Interesado	Josefa	Casells	nan	nan
579	675381	Cónyuge	José	Guitarte	nan	nan
580	675381	Padre	nan	Casells	nan	nan
581	675381	Madre	nan	nan	nan	nan
582	675381	Abuelo Paterno	nan	nan	nan	nan
-- [DATA SKIPPED FOR ab: 17419991 lines approx]
\.


--
-- TOC entry 2844 (class 0 OID 655360)
-- Dependencies: 203
-- Data for Name: Registros; Type: TABLE DATA; Schema: ab; Owner: postgres
--

COPY ab."Registros" ("Registro", "Sacramentos", "Libro", "Folio", "Asiento", "Sexo", "Subcon") FROM stdin;
675381	4	LM 1760-1766	017v	nan	M	0
675434	4	LM 1760-1766	017v	nan	H	0
96356	4	LM 1816-1825	109r	18	H	0
96405	4	LM 1816-1825	109r	18	M	0
21981	1	LB 1866-1871	404	075	H	0
-- [DATA SKIPPED FOR ab: 2177506 lines approx]
\.


--
-- TOC entry 2845 (class 0 OID 655377)
-- Dependencies: 204
-- Data for Name: Sacramentos; Type: TABLE DATA; Schema: ab; Owner: postgres
--

COPY ab."Sacramentos" (id, "Sacramentos") FROM stdin;
1	Bautismo
2	Confirmación
3	
4	Matrimonio
5	Defunción
-- [DATA SKIPPED FOR ab: 1 lines approx]
\.


--
-- TOC entry 2856 (class 0 OID 0)
-- Dependencies: 205
-- Name: Personas_ID_seq; Type: SEQUENCE SET; Schema: ab; Owner: postgres
--

SELECT pg_catalog.setval('ab."Personas_ID_seq"', 18957409, true);


--
-- TOC entry 2714 (class 2606 OID 663606)
-- Name: DatosPersonales DatosPersonales_pkey; Type: CONSTRAINT; Schema: ab; Owner: postgres
--

ALTER TABLE ONLY ab."DatosPersonales"
    ADD CONSTRAINT "DatosPersonales_pkey" PRIMARY KEY (registro);


--
-- TOC entry 2712 (class 2606 OID 663562)
-- Name: Personas Personas_pkey; Type: CONSTRAINT; Schema: ab; Owner: postgres
--

ALTER TABLE ONLY ab."Personas"
    ADD CONSTRAINT "Personas_pkey" PRIMARY KEY ("ID");


--
-- TOC entry 2706 (class 2606 OID 655364)
-- Name: Registros Registros_pkey; Type: CONSTRAINT; Schema: ab; Owner: postgres
--

ALTER TABLE ONLY ab."Registros"
    ADD CONSTRAINT "Registros_pkey" PRIMARY KEY ("Registro");


--
-- TOC entry 2708 (class 2606 OID 655383)
-- Name: Sacramentos Sacramentos_Unicos; Type: CONSTRAINT; Schema: ab; Owner: postgres
--

ALTER TABLE ONLY ab."Sacramentos"
    ADD CONSTRAINT "Sacramentos_Unicos" UNIQUE ("Sacramentos");


--
-- TOC entry 2710 (class 2606 OID 655381)
-- Name: Sacramentos Sacramentos_pkey; Type: CONSTRAINT; Schema: ab; Owner: postgres
--

ALTER TABLE ONLY ab."Sacramentos"
    ADD CONSTRAINT "Sacramentos_pkey" PRIMARY KEY (id);


--
-- TOC entry 2716 (class 2606 OID 663902)
-- Name: Personas FKRegistros; Type: FK CONSTRAINT; Schema: ab; Owner: postgres
--

ALTER TABLE ONLY ab."Personas"
    ADD CONSTRAINT "FKRegistros" FOREIGN KEY (registro) REFERENCES ab."Registros"("Registro");


--
-- TOC entry 2717 (class 2606 OID 663607)
-- Name: DatosPersonales PK-FK; Type: FK CONSTRAINT; Schema: ab; Owner: postgres
--

ALTER TABLE ONLY ab."DatosPersonales"
    ADD CONSTRAINT "PK-FK" FOREIGN KEY (registro) REFERENCES ab."Registros"("Registro");


--
-- TOC entry 2715 (class 2606 OID 655384)
-- Name: Registros Sacramentos_FK; Type: FK CONSTRAINT; Schema: ab; Owner: postgres
--

ALTER TABLE ONLY ab."Registros"
    ADD CONSTRAINT "Sacramentos_FK" FOREIGN KEY ("Sacramentos") REFERENCES ab."Sacramentos"(id) NOT VALID;


--
-- TOC entry 2854 (class 0 OID 0)
-- Dependencies: 6
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO PUBLIC;


-- Completed on 2022-12-24 17:58:25

--
-- PostgreSQL database dump complete
--

