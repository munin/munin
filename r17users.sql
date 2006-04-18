--
-- PostgreSQL database dump
--

SET client_encoding = 'LATIN1';
SET check_function_bodies = false;
SET client_min_messages = warning;

SET search_path = public, pg_catalog;

--
-- Name: user_list_id_seq; Type: SEQUENCE SET; Schema: public; Owner: andreaja
--

SELECT pg_catalog.setval(pg_catalog.pg_get_serial_sequence('user_list', 'id'), 56, true);


--
-- Data for Name: user_list; Type: TABLE DATA; Schema: public; Owner: andreaja
--

COPY user_list (id, pnick, passwd, userlevel, posflags, negflags) FROM stdin;
29	delos	\N	100	\N	\N
30	shiva	\N	100	\N	\N
31	meganova	\N	100	\N	\N
32	valle	\N	100	\N	\N
33	dav	\N	100	\N	\N
34	benneh	\N	100	\N	\N
35	idler	\N	100	\N	\N
36	nora	\N	100	\N	\N
37	zzhou	\N	100	\N	\N
38	rob	\N	1000	\N	\N
39	rember	\N	100	\N	\N
41	heartless	\N	100	\N	\N
42	jerome`	\N	100	\N	\N
43	desse	\N	100	\N	\N
44	tesla	\N	100	\N	\N
45	greatjupp	\N	100	\N	\N
46	dunkelgraf	\N	100	\N	\N
47	jbg	\N	100	\N	\N
48	raging-retard	\N	100	\N	\N
49	svenn	\N	100	\N	\N
50	theberk	\N	100	\N	\N
51	rgat	\N	100	\N	\N
52	stoom	\N	100	\N	\N
53	imnotnetgamers	\N	100	\N	\N
54	nolez	\N	100	\N	\N
56	marty	\N	100	\N	\N
\.


--
-- PostgreSQL database dump complete
--

