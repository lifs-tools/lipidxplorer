pipeline {
    agent none
    options {
        skipStagesAfterUnstable()
    }
    stages {
        stage('Prepare') {
        }
        stage('Deliver') {
            agent {
                docker {
                    image "cdrx/pyinstaller-windows:python2"
                    args "-v /jenkins_home/jobs/lipidxplorer/workspace:/src --entrypoint=\'\'"
                    reuseNode true
                }
            }
            steps {
                sh 'pyinstaller --distpath="/src/LipidXplorer-1.2.8.${BUILD_NUMBER}" /src/LipidXplorer.spec'
            }
            post {
                success {
                    archiveArtifacts '/jenkins_home/jobs/pipeline_example/workspace/LipidXplorer-1.2.8.${BUILD_NUMBER}.zip'
                }
            }
        }
    }
}