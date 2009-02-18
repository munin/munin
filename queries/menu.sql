--
-- PostgreSQL database dump
--

-- Started on 2007-06-27 15:47:00 CEST

SET client_encoding = 'UTF8';
SET check_function_bodies = false;
SET client_min_messages = warning;

SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- TOC entry 1323 (class 1259 OID 25039)
-- Dependencies: 1650 1651 5
-- Name: menu; Type: TABLE; Schema: public; Owner: munin; Tablespace:
--

CREATE TABLE menu (
    id serial NOT NULL,
    name character varying(40) NOT NULL,
    url character varying(255) NOT NULL,
    userlevel integer DEFAULT 0 NOT NULL,
    orderkey integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.menu OWNER TO munin;

--
-- TOC entry 1656 (class 0 OID 0)
-- Dependencies: 1322
-- Name: menu_id_seq; Type: SEQUENCE SET; Schema: public; Owner: munin
--

SELECT pg_catalog.setval(pg_catalog.pg_get_serial_sequence('menu', 'id'), 1, false);


--
-- TOC entry 1654 (class 0 OID 25039)
-- Dependencies: 1323
-- Data for Name: menu; Type: TABLE DATA; Schema: public; Owner: munin
--

COPY menu (id, name, url, userlevel, orderkey) FROM stdin;
2	Defence	defence.php	100	20
3	Attack	attack.php	1	30
4	HC Tools	#	100	50
6	Scans	scans.php	0	35
1	Arbiter	arbiter_main.php	0	40
5	Member tools	index.php	0	10
\.


--
-- TOC entry 1653 (class 2606 OID 25045)
-- Dependencies: 1323 1323
-- Name: menu_pkey; Type: CONSTRAINT; Schema: public; Owner: munin; Tablespace:
--

ALTER TABLE ONLY menu
    ADD CONSTRAINT menu_pkey PRIMARY KEY (id);


-- Completed on 2007-06-27 15:47:01 CEST

--
-- PostgreSQL database dump complete
--

