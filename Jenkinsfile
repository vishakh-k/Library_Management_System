// =============================================================================
// Jenkinsfile – Library Management System CI/CD Pipeline
// Declarative pipeline for build → test → deploy workflow
// =============================================================================

pipeline {
    agent any

    environment {
        DOCKER_IMAGE    = 'library-management-system'
        DOCKER_TAG      = "${env.BUILD_NUMBER}"
        COMPOSE_PROJECT = 'lms'
        APP_URL         = 'http://localhost'
    }

    options {
        // Abort builds that take too long
        timeout(time: 30, unit: 'MINUTES')
        // Keep last 10 builds
        buildDiscarder(logRotator(numToKeepStr: '10'))
        // Do not run concurrent builds for the same branch
        disableConcurrentBuilds()
        // Prepend timestamps to console output
        timestamps()
    }

    stages {
        // -----------------------------------------------------------------
        // Stage 1 – Checkout source code
        // -----------------------------------------------------------------
        stage('Checkout') {
            steps {
                echo '📥  Checking out source code…'
                checkout scm
            }
        }

        // -----------------------------------------------------------------
        // Stage 2 – Install Python dependencies in a virtual-env
        // -----------------------------------------------------------------
        stage('Install Dependencies') {
            steps {
                echo '📦  Installing Python dependencies…'
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        // -----------------------------------------------------------------
        // Stage 3 – Lint / static analysis (optional but recommended)
        // -----------------------------------------------------------------
        stage('Code Quality') {
            steps {
                echo '🔍  Running code-quality checks…'
                sh '''
                    . venv/bin/activate
                    pip install flake8
                    flake8 --max-line-length=120 --exclude=venv,__pycache__,.git --count --statistics . || true
                '''
            }
        }

        // -----------------------------------------------------------------
        // Stage 4 – Run the test suite
        // -----------------------------------------------------------------
        stage('Run Tests') {
            steps {
                echo '🧪  Running tests with pytest…'
                sh '''
                    . venv/bin/activate
                    pytest tests/ \
                        --tb=short \
                        --junitxml=reports/test-results.xml \
                        -v
                '''
            }
            post {
                always {
                    // Publish JUnit results to Jenkins dashboard
                    junit allowEmptyResults: true, testResults: 'reports/test-results.xml'
                }
            }
        }

        // -----------------------------------------------------------------
        // Stage 5 – Build Docker image
        // -----------------------------------------------------------------
        stage('Build Docker Image') {
            steps {
                echo "🐳  Building Docker image ${DOCKER_IMAGE}:${DOCKER_TAG}…"
                sh """
                    docker build \
                        -t ${DOCKER_IMAGE}:${DOCKER_TAG} \
                        -t ${DOCKER_IMAGE}:latest \
                        .
                """
            }
        }

        // -----------------------------------------------------------------
        // Stage 6 – Tear down previous deployment
        // -----------------------------------------------------------------
        stage('Stop Old Containers') {
            steps {
                echo '🛑  Stopping old containers…'
                sh '''
                    docker-compose -p ${COMPOSE_PROJECT} down --remove-orphans || true
                '''
            }
        }

        // -----------------------------------------------------------------
        // Stage 7 – Deploy with Docker Compose
        // -----------------------------------------------------------------
        stage('Deploy') {
            steps {
                echo '🚀  Deploying application…'
                sh '''
                    docker-compose -p ${COMPOSE_PROJECT} up -d --build
                '''
            }
        }

        // -----------------------------------------------------------------
        // Stage 8 – Post-deploy health check
        // -----------------------------------------------------------------
        stage('Health Check') {
            steps {
                echo '❤️  Running health checks…'
                sh '''
                    echo "Waiting for services to stabilize…"
                    sleep 15

                    # --- Web app health check ---
                    MAX_RETRIES=10
                    RETRY_COUNT=0
                    until curl -sf --max-time 5 ${APP_URL} > /dev/null 2>&1; do
                        RETRY_COUNT=$((RETRY_COUNT + 1))
                        if [ "$RETRY_COUNT" -ge "$MAX_RETRIES" ]; then
                            echo "❌ Health check failed after ${MAX_RETRIES} attempts"
                            docker-compose -p ${COMPOSE_PROJECT} logs --tail=50
                            exit 1
                        fi
                        echo "  Attempt ${RETRY_COUNT}/${MAX_RETRIES} – retrying in 5s…"
                        sleep 5
                    done
                    echo "✅ Application is healthy and responding"

                    # --- Container status ---
                    echo ""
                    echo "=== Running containers ==="
                    docker-compose -p ${COMPOSE_PROJECT} ps
                '''
            }
        }
    }

    // =========================================================================
    // Post-build actions
    // =========================================================================
    post {
        success {
            echo '✅  Pipeline completed successfully – application deployed!'
        }
        failure {
            echo '❌  Pipeline failed – check stage logs above for details.'
            // Optionally roll back to the previous image:
            // sh 'docker-compose -p ${COMPOSE_PROJECT} down || true'
        }
        unstable {
            echo '⚠️  Pipeline unstable – some tests may have failed.'
        }
        always {
            // Archive test reports if they exist
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true

            // Clean up the workspace
            cleanWs()
        }
    }
}
