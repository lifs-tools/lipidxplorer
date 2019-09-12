pipeline {
    agent none
    options {
        skipStagesAfterUnstable()
    }
    stages {
        stage('Deliver') {

            steps {
                sh 'docker run --rm -v ${PWD}:/src cdrx/pyinstaller-windows:python2 pyinstaller --distpath="LipidXplorer-1.2.8.${BUILD_NUMBER}" LipidXplorer.spec'
            }
            post {
                success {
                    archiveArtifacts 'LipidXplorer-1.2.8.${BUILD_NUMBER}.zip'
                }
            }
        }
    }
}