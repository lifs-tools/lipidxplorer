pipeline {
    agent none
    options {
        skipStagesAfterUnstable()
    }
    stages {
        stage('Deliver') {
            agent {
                docker {
                    image 'cdrx/pyinstaller-windows:python2'
                }
            }
            steps {
                sh 'pyinstaller --distpath="LipidXplorer-1.2.8.${BUILD_NUMBER}" LipidXplorer.spec'
            }
            post {
                success {
                    archiveArtifacts 'LipidXplorer-1.2.8.${BUILD_NUMBER}.zip'
                }
            }
        }
    }
}