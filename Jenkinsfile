pipeline {
    agent none
    options {
        skipStagesAfterUnstable()
    }
    stages {
        stage('Deliver') {
            agent {
                docker {
                    image "cdrx/pyinstaller-windows:python2"
                    args "-u root --privileged -v /var/jenkins_home/workspace/lipidxplorer:/src --entrypoint=''"
                    reuseNode true
                }
            }
            steps {
                sh 'pyinstaller --distpath="LipidXplorer-1.2.8.${BUILD_NUMBER}" LipidXplorer.spec'
            }
            post {
                success {
                    archiveArtifacts '/jenkins_home/jobs/pipeline_example/workspace/LipidXplorer-1.2.8.${BUILD_NUMBER}.zip'
                }
            }
        }
    }
}