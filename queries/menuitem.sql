PGDMP
         /                k        	   patools21    8.1.8    8.1.8     x           0    0    ENCODING    ENCODING    SET client_encoding = 'UTF8';
                       false            -           1259    25048    menuitem    TABLE �   CREATE TABLE menuitem (
    id serial NOT NULL,
    menu_id integer NOT NULL,
    name character varying(255) NOT NULL,
    url character varying(255) NOT NULL,
    userlevel integer DEFAULT 0 NOT NULL,
    orderkey integer DEFAULT 0 NOT NULL
);
    DROP TABLE public.menuitem;
       public         munin    false    1650    1651    5            y           0    0    menuitem_id_seq    SEQUENCE SET X   SELECT pg_catalog.setval(pg_catalog.pg_get_serial_sequence('menuitem', 'id'), 2, true);
            public       munin    false    1324            w          0    25048    menuitem 
   TABLE DATA           H   COPY menuitem (id, menu_id, name, url, userlevel, orderkey) FROM stdin;
    public       munin    false    1325   �       u           2606    25057    pkey_menuitem 
   CONSTRAINT M   ALTER TABLE ONLY menuitem
    ADD CONSTRAINT pkey_menuitem PRIMARY KEY (id);
 @   ALTER TABLE ONLY public.menuitem DROP CONSTRAINT pkey_menuitem;
       public         munin    false    1325    1325            v           2606    25058    fkey_menuitem_menu_id    FK CONSTRAINT n   ALTER TABLE ONLY menuitem
    ADD CONSTRAINT fkey_menuitem_menu_id FOREIGN KEY (menu_id) REFERENCES menu(id);
 H   ALTER TABLE ONLY public.menuitem DROP CONSTRAINT fkey_menuitem_menu_id;
       public       munin    false    1323    1325            w   �  x��RKo�0>ӿB�b�"��6;E�ۡ�t����L"��Ii�����+ú�`�4�	Ρ�/�#S���9@M����������+�!�Q���,��kf��F�f�>h�?���q�U�֬R+��E�B�|@c�68FC�Su�pa}M~(��\2�2��k�ulӋ ����Ρ���U}|v�!�j	f!�~���Im=�Sm_�?#���~�Z���ml�,��nd�{]=�cV#�a��es���!/�o}w�??)ƈ��o�,��z޳C�X.�B��᠝��2����E�&xA͸����	3(�;Iz�(D�+2�"�cP��쑻�|�v
��z����>��J��A�v����mf��k�l9��좑�m%7r��d<�'�.Л�(���g��B�&��'�V7�ϫ,�~�b     