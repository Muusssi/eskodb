pipeline {
    agent any

    stages {
        stage('Test') {
            steps {
                sh './run_robot.sh'
            }
        }
        stage('Deploy') {
            steps {
                echo 'Deploying....'
            }
        }
    }
}
