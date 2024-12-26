
.. _auth-rest-api:

==============================
QCFlow Authentication REST API
==============================


The QCFlow Authentication REST API allows you to create, get, update and delete users, 
experiment permissions and registered model permissions.
The API is hosted under the ``/api`` route on the QCFlow tracking server. For example, to list
experiments on a tracking server hosted at ``http://localhost:5000``, access
``http://localhost:5000/api/2.0/qcflow/users/create``.

.. important::
    The QCFlow REST API requires content type ``application/json`` for all POST requests.

.. contents:: Table of Contents
    :local:
    :depth: 1

===========================

.. _qcflowAuthServiceCreateUser:

Create User
===========

+-----------------------------+-------------+
|          Endpoint           | HTTP Method |
+=============================+=============+
| ``2.0/qcflow/users/create`` | ``POST``    |
+-----------------------------+-------------+

.. _qcflowCreateUser:

Request Structure
-----------------

+------------+------------+-------------+
| Field Name |    Type    | Description |
+============+============+=============+
| username   | ``STRING`` | Username.   |
+------------+------------+-------------+
| password   | ``STRING`` | Password.   |
+------------+------------+-------------+

.. _qcflowCreateUserResponse:

Response Structure
------------------

+------------+-------------------+----------------+
| Field Name |       Type        |  Description   |
+============+===================+================+
| user       | :ref:`qcflowUser` | A user object. |
+------------+-------------------+----------------+

===========================

.. _qcflowAuthServiceGetUser:

Get User
========

+--------------------------+-------------+
|         Endpoint         | HTTP Method |
+==========================+=============+
| ``2.0/qcflow/users/get`` | ``GET``     |
+--------------------------+-------------+

.. _qcflowGetUser:

Request Structure
-----------------

+------------+------------+-------------+
| Field Name |    Type    | Description |
+============+============+=============+
| username   | ``STRING`` | Username.   |
+------------+------------+-------------+

.. _qcflowGetUserResponse:

Response Structure
------------------

+------------+-------------------+----------------+
| Field Name |       Type        |  Description   |
+============+===================+================+
| user       | :ref:`qcflowUser` | A user object. |
+------------+-------------------+----------------+

===========================

.. _qcflowAuthServiceUpdateUserPassword:

Update User Password
====================

+--------------------------------------+-------------+
|               Endpoint               | HTTP Method |
+======================================+=============+
| ``2.0/qcflow/users/update-password`` | ``PATCH``   |
+--------------------------------------+-------------+

.. _qcflowUpdateUserPassword:

Request Structure
-----------------

+------------+------------+---------------+
| Field Name | Type       | Description   |
+============+============+===============+
| username   | ``STRING`` | Username.     |
+------------+------------+---------------+
| password   | ``STRING`` | New password. |
+------------+------------+---------------+

===========================

.. _qcflowAuthServiceUpdateUserAdmin:

Update User Admin
=================

+-----------------------------------+-------------+
|             Endpoint              | HTTP Method |
+===================================+=============+
| ``2.0/qcflow/users/update-admin`` | ``PATCH``   |
+-----------------------------------+-------------+

.. _qcflowUpdateUserAdmin:

Request Structure
-----------------

+------------+-------------+-------------------+
| Field Name |    Type     |    Description    |
+============+=============+===================+
| username   | ``STRING``  | Username.         |
+------------+-------------+-------------------+
| is_admin   | ``BOOLEAN`` | New admin status. |
+------------+-------------+-------------------+

===========================

.. _qcflowAuthServiceDeleteUser:

Delete User
===========

+-----------------------------+-------------+
|          Endpoint           | HTTP Method |
+=============================+=============+
| ``2.0/qcflow/users/delete`` | ``DELETE``  |
+-----------------------------+-------------+

.. _qcflowDeleteUser:

Request Structure
-----------------

+------------+------------+-------------+
| Field Name |    Type    | Description |
+============+============+=============+
| username   | ``STRING`` | Username.   |
+------------+------------+-------------+

===========================

.. _qcflowAuthServiceCreateExperimentPermission:

Create Experiment Permission
============================

+-----------------------------------------------+-------------+
|                   Endpoint                    | HTTP Method |
+===============================================+=============+
| ``2.0/qcflow/experiments/permissions/create`` | ``POST``    |
+-----------------------------------------------+-------------+

.. _qcflowCreateExperimentPermission:

Request Structure
-----------------

+---------------+-------------------------+----------------------+
|  Field Name   |          Type           |     Description      |
+===============+=========================+======================+
| experiment_id | ``STRING``              | Experiment id.       |
+---------------+-------------------------+----------------------+
| username      | ``STRING``              | Username.            |
+---------------+-------------------------+----------------------+
| permission    | :ref:`qcflowPermission` | Permission to grant. |
+---------------+-------------------------+----------------------+

.. _qcflowCreateExperimentPermissionResponse:

Response Structure
------------------

+-----------------------+-----------------------------------+----------------------------------+
|      Field Name       |               Type                |           Description            |
+=======================+===================================+==================================+
| experiment_permission | :ref:`qcflowExperimentPermission` | An experiment permission object. |
+-----------------------+-----------------------------------+----------------------------------+

===========================

.. _qcflowAuthServiceGetExperimentPermission:

Get Experiment Permission
=========================

+--------------------------------------------+-------------+
|                  Endpoint                  | HTTP Method |
+============================================+=============+
| ``2.0/qcflow/experiments/permissions/get`` | ``GET``     |
+--------------------------------------------+-------------+

.. _qcflowGetExperimentPermission:

Request Structure
-----------------

+---------------+------------+----------------+
|  Field Name   |    Type    |  Description   |
+===============+============+================+
| experiment_id | ``STRING`` | Experiment id. |
+---------------+------------+----------------+
| username      | ``STRING`` | Username.      |
+---------------+------------+----------------+

.. _qcflowGetExperimentPermissionResponse:

Response Structure
------------------

+-----------------------+-----------------------------------+----------------------------------+
|      Field Name       |               Type                |           Description            |
+=======================+===================================+==================================+
| experiment_permission | :ref:`qcflowExperimentPermission` | An experiment permission object. |
+-----------------------+-----------------------------------+----------------------------------+

===========================

.. _qcflowAuthServiceUpdateExperimentPermission:

Update Experiment Permission
============================

+-----------------------------------------------+-------------+
|                   Endpoint                    | HTTP Method |
+===============================================+=============+
| ``2.0/qcflow/experiments/permissions/update`` | ``PATCH``   |
+-----------------------------------------------+-------------+

.. _qcflowUpdateExperimentPermission:

Request Structure
-----------------

+---------------+-------------------------+--------------------------+
|  Field Name   |          Type           |       Description        |
+===============+=========================+==========================+
| experiment_id | ``STRING``              | Experiment id.           |
+---------------+-------------------------+--------------------------+
| username      | ``STRING``              | Username.                |
+---------------+-------------------------+--------------------------+
| permission    | :ref:`qcflowPermission` | New permission to grant. |
+---------------+-------------------------+--------------------------+

===========================

.. _qcflowAuthServiceDeleteExperimentPermission:

Delete Experiment Permission
============================

+-----------------------------------------------+-------------+
|                   Endpoint                    | HTTP Method |
+===============================================+=============+
| ``2.0/qcflow/experiments/permissions/delete`` | ``DELETE``  |
+-----------------------------------------------+-------------+

.. _qcflowDeleteExperimentPermission:

Request Structure
-----------------

+---------------+------------+----------------+
|  Field Name   |    Type    |  Description   |
+===============+============+================+
| experiment_id | ``STRING`` | Experiment id. |
+---------------+------------+----------------+
| username      | ``STRING`` | Username.      |
+---------------+------------+----------------+

===========================

.. _qcflowAuthServiceCreateRegisteredModelPermission:

Create Registered Model Permission
==================================

+-----------------------------------------------------+-------------+
|                      Endpoint                       | HTTP Method |
+=====================================================+=============+
| ``2.0/qcflow/registered-models/permissions/create`` | ``CREATE``  |
+-----------------------------------------------------+-------------+

.. _qcflowCreateRegisteredModelPermission:

Request Structure
-----------------

+------------+-------------------------+------------------------+
| Field Name |          Type           |      Description       |
+============+=========================+========================+
| name       | ``STRING``              | Registered model name. |
+------------+-------------------------+------------------------+
| username   | ``STRING``              | Username.              |
+------------+-------------------------+------------------------+
| permission | :ref:`qcflowPermission` | Permission to grant.   |
+------------+-------------------------+------------------------+

.. _qcflowCreateRegisteredModelPermissionResponse:

Response Structure
------------------

+-----------------------------+----------------------------------------+---------------------------------------+
|         Field Name          |                  Type                  |              Description              |
+=============================+========================================+=======================================+
| registered_model_permission | :ref:`qcflowRegisteredModelPermission` | A registered model permission object. |
+-----------------------------+----------------------------------------+---------------------------------------+

===========================

.. _qcflowAuthServiceGetRegisteredModelPermission:

Get Registered Model Permission
===============================

+--------------------------------------------------+-------------+
|                     Endpoint                     | HTTP Method |
+==================================================+=============+
| ``2.0/qcflow/registered-models/permissions/get`` | ``GET``     |
+--------------------------------------------------+-------------+

.. _qcflowGetRegisteredModelPermission:

Request Structure
-----------------

+------------+------------+------------------------+
| Field Name |    Type    |      Description       |
+============+============+========================+
| name       | ``STRING`` | Registered model name. |
+------------+------------+------------------------+
| username   | ``STRING`` | Username.              |
+------------+------------+------------------------+

.. _qcflowGetRegisteredModelPermissionResponse:

Response Structure
------------------

+-----------------------------+----------------------------------------+---------------------------------------+
|         Field Name          |                  Type                  |              Description              |
+=============================+========================================+=======================================+
| registered_model_permission | :ref:`qcflowRegisteredModelPermission` | A registered model permission object. |
+-----------------------------+----------------------------------------+---------------------------------------+

===========================

.. _qcflowAuthServiceUpdateRegisteredModelPermission:

Update Registered Model Permission
==================================

+-----------------------------------------------------+-------------+
|                      Endpoint                       | HTTP Method |
+=====================================================+=============+
| ``2.0/qcflow/registered-models/permissions/update`` | ``PATCH``   |
+-----------------------------------------------------+-------------+

.. _qcflowUpdateRegisteredModelPermission:

Request Structure
-----------------

+------------+-------------------------+--------------------------+
| Field Name |          Type           |       Description        |
+============+=========================+==========================+
| name       | ``STRING``              | Registered model name.   |
+------------+-------------------------+--------------------------+
| username   | ``STRING``              | Username.                |
+------------+-------------------------+--------------------------+
| permission | :ref:`qcflowPermission` | New permission to grant. |
+------------+-------------------------+--------------------------+

===========================

.. _qcflowAuthServiceDeleteRegisteredModelPermission:

Delete Registered Model Permission
==================================

+-----------------------------------------------------+-------------+
|                      Endpoint                       | HTTP Method |
+=====================================================+=============+
| ``2.0/qcflow/registered-models/permissions/delete`` | ``DELETE``  |
+-----------------------------------------------------+-------------+

.. _qcflowDeleteRegisteredModelPermission:

Request Structure
-----------------

+------------+------------+------------------------+
| Field Name |    Type    |      Description       |
+============+============+========================+
| name       | ``STRING`` | Registered model name. |
+------------+------------+------------------------+
| username   | ``STRING`` | Username.              |
+------------+------------+------------------------+


.. _auth-rest-struct:

Data Structures
===============


.. _qcflowUser:

User
----

+------------------------------+----------------------------------------------------+------------------------------------------------------------------+
|          Field Name          |                        Type                        |                            Description                           |
+==============================+====================================================+==================================================================+
| id                           | ``STRING``                                         | User ID.                                                         |
+------------------------------+----------------------------------------------------+------------------------------------------------------------------+
| username                     | ``STRING``                                         | Username.                                                        |
+------------------------------+----------------------------------------------------+------------------------------------------------------------------+
| is_admin                     | ``BOOLEAN``                                        | Whether the user is an admin.                                    |
+------------------------------+----------------------------------------------------+------------------------------------------------------------------+
| experiment_permissions       | An array of :ref:`qcflowExperimentPermission`      | All experiment permissions explicitly granted to the user.       |
+------------------------------+----------------------------------------------------+------------------------------------------------------------------+
| registered_model_permissions | An array of :ref:`qcflowRegisteredModelPermission` | All registered model permissions explicitly granted to the user. |
+------------------------------+----------------------------------------------------+------------------------------------------------------------------+

.. _qcflowPermission:

Permission
----------

Permission of a user to an experiment or a registered model.

+----------------+--------------------------------------+
|      Name      |             Description              |
+================+======================================+
| READ           | Can read.                            |
+----------------+--------------------------------------+
| EDIT           | Can read and update.                 |
+----------------+--------------------------------------+
| MANAGE         | Can read, update, delete and manage. |
+----------------+--------------------------------------+
| NO_PERMISSIONS | No permissions.                      |
+----------------+--------------------------------------+

.. _qcflowExperimentPermission:

ExperimentPermission
--------------------

+---------------+-------------------------+---------------------+
|  Field Name   |          Type           |     Description     |
+===============+=========================+=====================+
| experiment_id | ``STRING``              | Experiment id.      |
+---------------+-------------------------+---------------------+
| user_id       | ``STRING``              | User id.            |
+---------------+-------------------------+---------------------+
| permission    | :ref:`qcflowPermission` | Permission granted. |
+---------------+-------------------------+---------------------+

.. _qcflowRegisteredModelPermission:

RegisteredModelPermission
-------------------------

+------------+-------------------------+------------------------+
| Field Name |          Type           |      Description       |
+============+=========================+========================+
| name       | ``STRING``              | Registered model name. |
+------------+-------------------------+------------------------+
| user_id    | ``STRING``              | User id.               |
+------------+-------------------------+------------------------+
| permission | :ref:`qcflowPermission` | Permission granted.    |
+------------+-------------------------+------------------------+
