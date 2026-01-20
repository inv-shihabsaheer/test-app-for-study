pipeline {
  agent any

  /***********************
   * PARAMETERS
   ***********************/
  parameters {
    booleanParam(
      name: 'CREATE_CLUSTER',
      defaultValue: true,
      description: 'Create GKE cluster if it does not exist'
    )
  }

  /***********************
   * ENVIRONMENT
   ***********************/
  environment {
    PROJECT_ID    = "curser-project"
    REGION        = "us-central1"
    AR_REPO       = "my-artifact-repo"
    IMAGE_NAME    = "myapp"
    CLUSTER       = "my-gke-cluster"

    HELM_REPO_URL = "https://github.com/inv-shihabsaheer/test-app-for-study-helm-chart.git"
    HELM_REPO_DIR = "helm-repo"
    HELM_CHART    = "myapp"
  }

  stages {

    /***********************
     * CHECKOUT
     ***********************/
    stage('Checkout App Repo') {
      steps {
        checkout scm
      }
    }

    /***********************
     * AUTH + CLUSTER CREATE
     ***********************/
    stage('Create GKE Cluster (If Needed)') {
      when {
        expression { return params.CREATE_CLUSTER }
      }
      steps {
        withCredentials([
          file(credentialsId: 'GCP_SA_KEY', variable: 'GCP_KEY_FILE')
        ]) {
          sh """
            set -e

            echo "Authenticating to GCP..."
            gcloud auth activate-service-account --key-file="\$GCP_KEY_FILE"
            gcloud config set project ${PROJECT_ID}

            echo "Checking if GKE cluster exists..."
            if gcloud container clusters describe ${CLUSTER} \
              --region ${REGION} \
              --project ${PROJECT_ID} >/dev/null 2>&1; then
              echo "✅ GKE cluster already exists"
            else
              echo "🚀 Creating GKE cluster ${CLUSTER}..."

              gcloud container clusters create ${CLUSTER} \
                --region ${REGION} \
                --num-nodes 2 \
                --machine-type e2-medium \
                --project ${PROJECT_ID}

              echo "✅ GKE cluster created"
            fi
          """
        }
      }
    }

    /***********************
     * IMAGE TAG
     ***********************/
    stage('Generate Image Tag') {
      steps {
        script {
          def sha = sh(
            script: 'git rev-parse --short HEAD',
            returnStdout: true
          ).trim()

          env.IMAGE_TAG = "${sha}-${env.BUILD_NUMBER}"
          echo "Image tag: ${env.IMAGE_TAG}"
        }
      }
    }

    /***********************
     * BUILD & PUSH
     ***********************/
    stage('Build & Push Image') {
      steps {
        script {
          env.IMAGE_URI =
            "${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/${IMAGE_NAME}:${env.IMAGE_TAG}"

          withCredentials([
            file(credentialsId: 'GCP_SA_KEY', variable: 'GCP_KEY_FILE')
          ]) {
            sh """
              set -e

              echo "Authenticating to GCP..."
              gcloud auth activate-service-account --key-file="\$GCP_KEY_FILE"
              gcloud config set project ${PROJECT_ID}

              echo "Configuring Docker auth..."
              gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

              echo "Building image..."
              docker build --no-cache -t ${IMAGE_URI} .

              echo "Pushing image..."
              docker push ${IMAGE_URI}
            """
          }
        }
      }
    }

    /***********************
     * GITOPS UPDATE
     ***********************/
    stage('Update Helm Repo Image Tag (GitOps)') {
      steps {
        withCredentials([
          string(credentialsId: 'GITHUB_TOKEN', variable: 'GITHUB_TOKEN')
        ]) {
          sh """
            set -e

            rm -rf ${HELM_REPO_DIR}
            git clone https://x-access-token:\$GITHUB_TOKEN@github.com/inv-shihabsaheer/test-app-for-study-helm-chart.git ${HELM_REPO_DIR}

            cd ${HELM_REPO_DIR}/${HELM_CHART}

            sed -i 's|^  repository:.*|  repository: ${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/${IMAGE_NAME}|' values.yaml
            sed -i 's|^  tag:.*|  tag: ${IMAGE_TAG}|' values.yaml

            git config user.name "Jenkins CI"
            git config user.email "jenkins@ci.local"

            git add values.yaml
            git commit -m "ci: update image tag to ${IMAGE_TAG}" || exit 0
            git push origin main
          """
        }
      }
    }

    /***********************
     * DEPLOY
     ***********************/
    stage('Deploy using Helm') {
      steps {
        withCredentials([
          file(credentialsId: 'GCP_SA_KEY', variable: 'GCP_KEY_FILE')
        ]) {
          sh """
            set -e

            gcloud auth activate-service-account --key-file="\$GCP_KEY_FILE"
            gcloud config set project ${PROJECT_ID}

            gcloud container clusters get-credentials ${CLUSTER} \
              --region ${REGION} \
              --project ${PROJECT_ID}

            helm upgrade --install myapp ${HELM_REPO_DIR}/${HELM_CHART} \
              --set image.repository=${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/${IMAGE_NAME} \
              --set image.tag=${IMAGE_TAG}
          """
        }
      }
    }
  }

  /***********************
   * POST
   ***********************/
  post {
    success {
      echo "✅ Pipeline completed successfully"
    }
    failure {
      echo "❌ Pipeline failed"
    }
    always {
      cleanWs()
    }
  }
}
