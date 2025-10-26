pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                script {
                    try {
                        echo 'Building..'
                        build job: 'Build', waitForStart: true, wait: true
                    } catch (err) {
                        echo "Error in Build stage: ${err}"
                        currentBuild.result = 'FAILURE'
                        error("Stopping pipeline due to build failure.")
                    }
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    try {
                        echo 'Deploying..'
                        build job: 'Deploy', waitForStart: true, wait: true
                    } catch (err) {
                        echo "Error in Deploy stage: ${err}"
                        currentBuild.result = 'FAILURE'
                    }
                }
            }
        }

        stage('Test') {
            steps {
                script {
                    try {
                        echo 'Testing..'
                        build job: 'Test', waitForStart: true, wait: true
                    } catch (err) {
                        echo "Error in Test stage: ${err}"
                    }
                }
            }
        }

        stage('Release') {
            steps {
                script {
                    try {
                        echo 'Releasing..'
                        build job: 'Release', waitForStart: true, wait: true
                    } catch (err) {
                        echo "Error in Release stage: ${err}"
                    }
                }
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed — check logs for details.'
        }
        always {
            echo 'Pipeline finished (success or failure).'
        }
    }
}
