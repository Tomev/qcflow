Official QCFlow Docker Image
============================

The official QCFlow Docker image is available on GitHub Container Registry at https://ghcr.io/qcflow/qcflow.

.. code-block:: shell

    export CR_PAT=YOUR_TOKEN
    echo $CR_PAT | docker login ghcr.io -u USERNAME --password-stdin
    # Pull the latest version
    docker pull ghcr.io/qcflow/qcflow
    # Pull 2.0.1
    docker pull ghcr.io/qcflow/qcflow:v2.0.1
