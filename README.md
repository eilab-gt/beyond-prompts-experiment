# Storytelling Domain

This is the repository holding code we used in the experiments for "Beyond Prompts: Exploring the Design Space of Mixed-Initiative Co-creativity Systems".

## Try the exemplar application
- All the scripts are located `StorytellingDomain/Scripts`.
  - You need to run the scripts from that directory (working directory).
- Set up Addons
  - Run the script `setup_addon_server.sh`, or review it if you wish to download models to other folders.
    - If you do choose to put models somewhere else, you need to modify `StartAddonServer.py` accordingly.
To set this repository up:
- Set up environments
  - Create a conda env / virtual env named `storytelling-domain-for-creative-wand`
    - If you wish to use a different name, the `run-` scripts needs to adapt to it. 
  - Clone the Creative Wand framework (https://github.com/eilab-gt/CreativeWand)
  - `cd` to the Creative Wand framework
  - `pip install -e .`
  - Then, `pip install -r requirements.txt`
  - If your `conda` env does not contain `python` yet, run `conda install python`. We developed under `3.10`.
- Start the servers
  - Run the scripts `run_addon_server.sh` and `run_backend_server.sh` 
    - By default we load GPT-J, which requires 24G of VMem or more.
    - Alternatively you can run the `run_addon_server_smaller_model.sh` with 8G VMem with GPT2.
      - The quality of generation will be poorer.
  - If you wish to run it manually:
    - You need to add `StorytellingDomain/` to your `PYTHONPATH`. 
    - The backend entry point is `StorytellingDomain/
Application/Deployment/StartExperiment.py`
    - and `StorytellingDomain/
Application/Deployment/StartAddonServer.py`
  - Run `web-frontend/web-interface/run_http_server.sh`
  - Manual setup: The frontend entry point is `npm run start` with `web-frontend/package.json`
    - The first time you run it you need to do `npm install` to for `js` dependencies.
    - You may also need to install `conda install nodejs==18.11.0` (Or any newer versions)
- Use the system
  - Access your Creative Wand at http://localhost:3000/?mode=s2_f&pid=test .
    - `mode` is defined in StorytellingDomain/Application/Deployment/Presets/StoryPresets.py.
    - The modes featured in the experiments are:
      - `s2_f` for the "Full" system;
      - `s2_g` for the "Global-only ablation" system;
      - `s2_l` for the "Local-only ablation" system;
      - `s2_e` for the "Elaboration-only ablation" system;
      - `s2_r` for the "Reflection-only ablation" system;
      - `s2_h` for the "Human-Initiated-only ablation" system;
      - `s2_a` for the "Agent/AI-Initiated-only ablation" system;
    - `pid` was used to associate sessions with participants answering questionnaires.

## Add your own Communications
Check `StorytellingDomain/Application/Deployment/Presets/StoryPresets.py` on how modes are defined; Starting there, we have documents on functions that will walk you through the rest of the system.

## Set up HTTPS access (optional)
If you wish to add a certificate so that the sites can operate in HTTPS
- Pass `-s` to `StartExperiment.py`
- In `WebFrontendServer.py` set the paths to the certificates
- Set environments `HTTPS=true;SSL_CRT_FILE=<your fullchain.pem>;SSL_KEY_FILE=<your privkey.pem>` for the node frontend.