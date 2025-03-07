# developerhub-agentic-demo

First you need an OpenShift cluster with the required dependencies, it can be installed with the validated patter at:
https://github.com/luis5tb/multicloud-gitops/tree/rhdh-demo (note the `rhdh-demo` branch):

```bash
$ git clone https://github.com/luis5tb/multicloud-gitops
$ cd multicloud-gitops
$ git checkout rhdh-demo

# Adjust secrets as needed
$ cat values-secret.yaml.template
  # Database login credentials and configuration
  - name: modelregistry-keys
    fields:
    - name: database-user
      value: modelregistry_user
    - name: database-host
      value: modelregistrydb
    - name: database-db
      value: modelregistrydb
    - name: database-master-user
      value: modelregistry_user
    - name: database-password
      value: model-registry-user-123
    - name: database-root-password
      value: model-registry-user-123
    - name: database-master-password
      value: model-registry-user-123

  # Red Hat DeveloperHub Git Authentication
  - name: rhdh-keys
    fields:
    - name: BACKEND_SECRET
      value: rhdh_1_2_3
    - name: GH_ACCESS_TOKEN
      value: XXXX
    - name: GH_CLIENT_ID
      value: XXX
    - name: GH_CLIENT_SECRET
      value: XXX

  # Webhook configuration on RHDH generated git repositories
  - name: github-keys
    fields:
    - name: github_pat
      value: XXXX
    - name: webhook_secret
      value: XXXX

  # HuggingFace token (when using HF and S3 instead of OCI for model storage)
  - name: huggingface-keys
    fields:
    - name: hf_token
      value: XXXX
$ cp values-secret.yaml.template ~/.config/hybrid-cloud-patterns/values-secret-multicloud-gitops.yaml

# And trigger the pattern installation
$ ./pattern.sh make install

# If you need to regenerate/update the secrets, just update values-secret.yaml.template and load them
$  cp values-secret.yaml.template ~/.config/hybrid-cloud-patterns/values-secret-multicloud-gitops.yaml
$  ./pattern.sh make load-secrets

# To use VectorDB from Azure, add the next keys and re-load the secrets
# (or have them before triggering the make install)
# If a different VectorDB provider is to be use, use the same name but with the right name/value pairs
$ cat values-secret.yaml.template
  - name: vectordb-keys
    fields:
    - name: VECTORDB_PROVIDER
      value: AZURE
    - name: AZURE_AI_SEARCH_SERVICE_NAME
      value: XXXX
    - name: AZURE_AI_SEARCH_API_KEY
      value: XXXX
    - name: AZURE_AI_INDEX_NAME
      value: XXXX
# If you want to use AWS VectorDB (KnowledgeBase), then you would need to add
$ cat values-secret.yaml.template
  - name: vectordb-keys
    fields:
    - name: VECTORDB_PROVIDER
      value: AWS
    - name: AWS_KNOWLEDGE_BASE_ID
      value: XXXX
    - name: AWS_REGION_NAME
      value: eu-west-1
    - name: AWS_ACCESS_KEY_ID
      value: XXXX
    - name: AWS_SECRET_ACCESS_KEY
      value: XXXX
$  cp values-secret.yaml.template ~/.config/hybrid-cloud-patterns/values-secret-multicloud-gitops.yaml
$  ./pattern.sh make load-secrets
```

The template will be automatically imported, but you can clone it, modify it and then import the template into your deployed Red Hat Developer Hub and instantiate it. It will create two repositories in your Git account:
- git repo with the source code for the agent
- gitops repo with the resources being created using helm and argocd applications for deploying the demo resources:
  - Build pipeline for the agent image
  - LLM at OpenShift AI
  - Agent at OpenShift
  - TrustyAI evaluation job at OpenShift AI
  - LlamaStack distribution building and server deploying


## How to enable RHDH GitHub Authentication (GH Access token, cliend_id and client_secret)

There are two ways you can approach setting up GitHub authentication. The simplest way (which is not recommended for production because you would not normally put tokens and secrets directly into the config) is quick and easy, but doesn’t show you how to set up a GitHub organization, which will be needed for groups of people accessing Developer Hub. To use this method, do the following:

- Go to https://github.com and log in with your GitHub credentials.
- Visit https://github.com/settings/tokens/new to generate a new "classic" token.
- Now give the Token a name you will remember in the Note box.
- Tick the Repo box to allow this token access to the repositories. Doing this allows Developer Hub to write a repo.
- Select Generate Token and Copy the token details and save them. You will not see them again. This is your ACCESS_TOKEN.
- Now visit https://github.com/settings/applications/new to register a new OAuth App. Make sure you have created an OAuth App, not a Github App.
- Enter your developer hub application route URL in the Homepage URL input. This value is the default URL you are taken to when you enter Red Hat Developer Hub.
- In the OAuth App creation page, enter a memorable name.
- Ensure that the Callback URL in your GitHub application is configured as follows: https://redhat-developer-hub-<NAMESPACE_NAME\>.<OPENSHIFT_ROUTE_HOST\>/api/auth/github/handler/frame
- Under Webhook, uncheck the Active box.
- Click Create GitHub App to create the app. This will take you to the About screen.
- Under Client Secrets, click Generate a new client secret.
- Copy and save both CLIENT_ID and Client Secrets.

The recommended way to configure it is available at [Red Hat Developer Hub GitHub Authentication Configuration](https://docs.redhat.com/en/documentation/red_hat_developer_hub/1.4/html/authentication/authenticating-with-github#enabling-authentication-with-github)

## How to create Webhook secret and github_pat

  - Visit https://github.com/settings/tokens/new to generate a new "classic" token.
  - Now give the Token a name you will remember in the Note box.
  - Tick the admin:redpo_hook to allow this token to manage webhooks
  - Select Generate Token and Copy the token details and save them. You will not see them again. This is your github_pat and webhook_token.


## How to build an OCI ModelCar container from HuggingFace

[Build and deploy a ModelCar container in OpenShift AI](https://developers.redhat.com/articles/2025/01/30/build-and-deploy-modelcar-container-openshift-ai#)