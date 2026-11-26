from pathlib import Path
from unittest.mock import patch
import ast
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ID = 'forensic-server-panel'
sys.path.insert(0, str(ROOT / 'scripts'))

# Explicitly reviewed hash transitions for this user-requested addition only.
# Historical preservation reports stay immutable; all other paths retain their old checks.
APPROVED_TRANSITIONS = {
    'src/content/knowledge/forensic-method-index.md': (
        'baf6e52d15aa87146dc91fa9a6713abbfc65b5bd75e5a510566d90089e933fdb',
        '4b903f06390827b3c6bede9d30dd80a1f99aaf52a615fe8d946050e554233f31'),
    'src/content-curation/forensic-method-index.md': (
        'd221104a144c83363de30223084af728d1f6bcbb182a8e9f0dc3bbc430565c6b',
        '94a639cb73e11a241d4907088fca3b93c9e91797a6fbec0f70d7b48ed4104208'),
    'src/content/knowledge/disk-evidence.md': (
        '453b79f491cee6dfd858dca1e054ff465a400587752c6aaed76215635d0ccb80',
        '91b6ed5eed4bd8230d176aa1723ae272d795f31c7f3a881b43b81091f2bbc1e1'),
    'src/content-curation/disk-evidence.md': (
        '4439ab18a884e75af393049c098cc84a6a8669cb282e298ed2bd0f83a7ec5490',
        '70b15a58b7cc37777842a13b86f80fbf025d323c0c4484041b4c8d01ce3bff96'),
    'src/content/knowledge/forensic-crypto-account-chains.md': (
        '5bb79b5ddf7448834df2b93bf9359d9cc6f889c60dd6ccc8d86aee92d4c2f650',
        '706631045252efb37bccc45a8853942e08b49ecca280f61a917bd0ccf0926da8'),
    'src/content-curation/forensic-crypto-account-chains.md': (
        'f1a562583e82306f70e6d60f09632db7399910da46143f2405d70d32426d917c',
        'b88a0f7cf383826190bd0b8955c5923c476d0d8e90ee7155780cfd9111e37c30'),
    'src/content/knowledge/forensic-crypto-bitcoin.md': (
        '42a77961bc8fca44cc0b3f023c27e9f9b36822913feaf7e69d45aa1b3f876fe6',
        '589d5843d55fec26aa07789d08409cb145336cb86cc86a4a3baf9abe595f13a0'),
    'src/content-curation/forensic-crypto-bitcoin.md': (
        '73d323c3ceeca1add799ea1571e6c4730c0be0662817c07b5f5977e3f2b4012a',
        '741269821594908623e66e3fd21103fe056cb957a1c607da2ccc9fea5af5a5be'),
    'src/content/knowledge/forensic-crypto-foundations.md': (
        'caa347e04cdec0b5d5a748e2ec25ddaf9bee765de724dc1557643132c36a414e',
        '0adfe7be5e757734ac24920c6e8bf71b61c6248b2cfca8143ce5506d25d27005'),
    'src/content-curation/forensic-crypto-foundations.md': (
        '37b1eba6a5e63a8204c9eadd3af03809f0087a89d732c2ff8dbd1aa5c56c42fe',
        '0e3f7ddc0b18f873938d316320bf1572d2804f722b903eddba0204768bfc74d3'),
    'src/content/knowledge/forensic-media.md': (
        '59472eea74f1d44baeea0743ba431162c6ea43ce98454760a73a0486cf6aac98',
        '1f9a2f9172570fd9b5b09d05110dc8ce171770c57da749fe4b87b64de1ae2a3c'),
    'src/content-curation/forensic-media.md': (
        '20c396a6537889702d8015635d387fa8c9caed658ab4daede4040f59fe6f237d',
        'd5f923d4ab625784172a28a9a94609624bdecbb9133ddbcddd00401f3e3c3794'),
    'src/content/knowledge/forensic-documents.md': (
        '4e3ba810923275ffda0daa459589caccd8974e83e84634470d8ea698f2f3c971',
        'ae155eac7befad1e7b4e8fd143cb6cea3838a4f6db5af9396d9db77af2f50db7'),
    'src/content-curation/forensic-documents.md': (
        '245d9f159d5756ac4cdd4d07029ad43f4cc7edf38b7bb8a5a58e206be1cd613e',
        '68e1e691a582caa48ce9050941b5f3d83b2929ea5d083102592a37164185cc7a'),
    'src/content/knowledge/forensic-file-recovery.md': (
        'a29e6673ecb8172390a20894d1fde48b70a51efe3e65e64d4cb4cfbea9ae5fb6',
        '939278ff53be9c3c814f7d2f6e12c628456ea82cedee821b21c62afca9491319'),
    'src/content-curation/forensic-file-recovery.md': (
        'a429fef5c1354ed638fe90256473771c5e35bfa415dd4fcfe652cfd2372182d0',
        '0fce8db51285344054fa6df152606b486726240f21ca9eeeae72dc959b7d2643'),
    'src/content/knowledge/forensic-guide-network.md': (
        '5881c3611d057b0b34bce655f967fe7b32064dfb2701b9a094dd2c9b669df846',
        '681667ace41db35969265a036e581c04afd56fe1f83fd798ad624d8d40f9f7a3'),
    'src/content-curation/forensic-guide-network.md': (
        'd878029474496ddc83e194e436cd4bc4db856e7d18199c3bc7ffcaf04d96c073',
        '0c9d440533fa96252032f6272b8a9442483270d3c7ee13896e2fc2d6d81a3129'),
    'src/content/knowledge/forensic-windows-artifacts.md': (
        '02b6152b099963cdc78000fa668dd3a04d5f3a9e88aef5b6633a5b8e1cb45a40',
        '75a0dd123dde1b24de63074f314fda3c3c859abcafdfb601e7b11e92088c038e'),
    'src/content-curation/forensic-windows-artifacts.md': (
        'a1f550ef38220e8c269b1190f550ebb69e2104a801cfa82013b1358ffa6936c1',
        '4da587c7971d16c2469b25b3478ffc00aa42345efce6f793a0d52b07c468cf5f'),
    'src/content/knowledge/forensic-memory-volatility.md': (
        'bdc8034550b7dd29c33313dbc23ef56d181a3dad9aac87b4872bb4058e8f8fd7',
        '49f7cac10caace0eb59854aa6c44934570c0961cb80d9ac2e7b61c2b83ceb7e9'),
    'src/content-curation/forensic-memory-volatility.md': (
        '98ccd6f1ab3603130e7996a665530ea97fec664e34d30adc572ce5338b7eef59',
        '0b75a4fb36a7e87810f0da32be75932062aa59ef0cfbef586d8a7d9013ec34f3'),
    'src/content/knowledge/forensic-memory-practice.md': (
        'a10eecadc4d118129ab2ad10f1e34a4207dfcbad0fda09fdc1817d1d9fc68901',
        '359291e0b7600d3dfbcaba603ccb0c86eb1ffa057657221f9ab403b974a67908'),
    'src/content-curation/forensic-memory-practice.md': (
        'baac681545bc7ea02b4d94500fb96a25c2053fdbcf29a95f4ebbd8e261524182',
        '4955b475ccdb4e0f3026eaa1a18a64496d1c50a2fd7f01af824419005ced8729'),
    'src/content/knowledge/forensic-memory.md': (
        '4a2c877bd93a3e0f95da3a86866d8670c265c4e2e383d51de460a9970faf0b12',
        'd6a86e0a70bd7e749965a6c9a35de297f3943e21c93a2813b9f2c3b8ba7d3760'),
    'src/content-curation/forensic-memory.md': (
        '22050d9003d024ead850c5d9bea0d6590e6594f806acc6d4b8d58425cadb60dc',
        'dd9348b6b44c58deb0c073f125819f5e2ee0bc8157e4442f28240ede288359e0'),
    'src/content/knowledge/forensic-xways-workflow.md': (
        'b15a9cc6d4f64071dc39a0a346d4ac2a01be0db603d1364bdc0b8fdfa3287c21',
        '2c008ebe4ef0105a5bc46d70e0f3bbb52900cd2f2ad0241425ba89f96de98c28'),
    'src/content-curation/forensic-xways-workflow.md': (
        '2bca5e6e95480235ecde2c9ee5284e01ccaaa53fba1a73681dd76251578a5e6c',
        '81638d77a312ef2cb35d9ce2826be7b0c8ffe1dc1c766bccae63d3629f7e0dce'),
    'src/content/knowledge/forensic-ios-tools.md': (
        '158e120588ceabc3b474c2160286b32a1e54b1d61aca4015ec6535dc81ecb96c',
        '096dbd66141857f2947ca8e0a0945c9452139c89f81f9575606d1993b247fa62'),
    'src/content-curation/forensic-ios-tools.md': (
        '41984c4297fd43d3f2271827e6bdae5a14896e51a7e285bca9639cab30730285',
        '0387fe043bc1335375172181e73e08dbb71dc6bb517de754884a9e9ddf6cd9e1'),
    'src/content/knowledge/forensic-android-tools.md': (
        '4b57921b27a4a1ae07ee436ba32fea9fa231bb10f02924fd4dd02af9a9b5cef6',
        '9306ed7bb186113a3fd696790d7b26c8e3f43429055184cb34f8eff81efb71e1'),
    'src/content-curation/forensic-android-tools.md': (
        'ffacf67e406fa7ac6afd24e55eed10ed77b8a0243c5bdf9d3247525a4c18e736',
        'ea6d9926dddbe08f3efd41d4f386619e91f8ebc69a658abb61efd526ba423b92'),
    'src/content/knowledge/forensic-android-forensics.md': (
        '4c1171056d411d7453f47907ae37afdddcef81f6b0c5b0cb0540e3090ce73157',
        'a11c742323195a9fb92fb954ce67bc53c3ad36c38f424fa025ac5b4b20476461'),
    'src/content-curation/forensic-android-forensics.md': (
        'b6212edc893fdd1531d9d6063bee76c6aebd36197c28c26947b21715288eb16b',
        'eda0346697dbeac2f66636cd1312c76b29d28cc439742aadc30034ed83dd332b'),
    'src/content/knowledge/forensic-guide-mobile.md': (
        '14938521f4c0dc557cad5e11ea9450222d8ae1bdb9bd11096c28970e539d20a9',
        'a954d132f876a5861f9dcd1cf99c1dadc3f654270daf5165155d0636ea5c147e'),
    'src/content-curation/forensic-guide-mobile.md': (
        'c522cc8d7f553b948da9766d37d86417857a341aeb4f81993d31154358123fce',
        'a4a85ed2ef2cfd2b7ad0f8a48e858b58b200bbb804f51b7c64e381340d785289'),
    'src/content-curation/fic-case-06.md': (
        '4e8e0989389ccdc6def08c849aa5361693e92737a4cc2b9527c2e38a58603e4b',
        '6e7f3c066acd9c2f136a11a5df0718aaf74be697af30fac5ee680b2935953329'),
    'src/content/knowledge/fic-case-06.md': (
        '088848b258af98b5d0cab06b435674b05a4dcf8181f6ca1f11b24abcf6716a7c',
        'c9547817c98965e70662466e704f9cdcb1117e85394a467771d1badbf8da49ea'),
    'src/content-curation/fic-case-07.md': (
        '88194230c69bf2845c63dc1eb3abe45fb87cc6b7ff6608f9af36b38b024cce38',
        'e0f072f7a581cd6cf7d7b8cbfb78299864d303fe0873504da9b397169af09cf1'),
    'src/content/knowledge/fic-case-07.md': (
        'c3eb529af08a6ea44c60517afc127d29faf6087b63df8f6a789c86ad25ca8e0d',
        '89670279174ab1e70ccfcbdb1cc184942198a56d8547df0149261740e76dc3b5'),
    'src/content-curation/fic-case-09.md': (
        '9d483fa1b3384952eda3ba93eabcb60829921d1d78b6a56322365cb100900dc9',
        '9bf5179394a60ee1a421b1930a1bdbbec1d6569eff45305289999180259f7287'),
    'src/content/knowledge/fic-case-09.md': (
        '3abe7d52f302f50fa39d086b644682a79fc5546a4c361faa43767ec021f16945',
        'f9ce6f3298e213f10eb07567aba1c5b12331d8a311b105876d7ce0a9dc9129ea'),
    'src/content-curation/forensic-android-storage.md': (
        '115c3ba0a456d4f2322a4e8d1fed8a5e2a15bb740e566fbaab4c05a726cfe6d5',
        'bc1ad6a5db04e25557b39b962782c99ab70abef735124c11577136d69d5a074a'),
    'src/content/knowledge/forensic-android-storage.md': (
        '3831ae32e0b03b268614bd5540d072e304d03c72819509691f5ebfd9eafe2719',
        'cd324b0adcf7810ba808f354c4beae529c80ed55e00954d67470591864a6100b'),
    'src/content-curation/forensic-ios-backup.md': (
        '7ec93ace3d2890d7c9e6fc178a37eb29143f169758e4ca1a6ee3246b5cb0db2f',
        '5ea9ae6ff03f72c9bfe9ae6ce25d8dda91c1bf587fbd49a6254e27c24c54a003'),
    'src/content/knowledge/forensic-ios-backup.md': (
        'bd0678b490afb5e85c8bb9c5dce83919e6172bcce4d3b7d8eba35727b5eaf5d9',
        '4f0f766d625d112fcf713d24586790b26b6ba2a448a423d6fdf117fbe586a5a9'),
    'src/content-curation/forensic-method-pitfalls.md': (
        '9e2dd3d090b99fb25ebf611db7004b2604217c5da0d9e2977fdf2cab2d235b57',
        '06f2a4173ed24ec48d7c9e2da5d3ed511e4e1ad0f732c26f178c7dde31a121ee'),
    'src/content/knowledge/forensic-method-pitfalls.md': (
        '4ccb8c9010713a47d6c3987023659bcaff88462ff5061176bbfde85e3de0bacc',
        'd08a1fa31f38516fffdcdacdcad941c556968d7c846a730d2c8874f3f01a9fdb'),
    'src/content-curation/forensic-mobile-apps.md': (
        'df3c4d01f050ab4f92be448d61ba9c4d89a8d9d79debb7532cf770cb751fde45',
        'a2be654111c287f558d67ce31ab435f2a81cf1f95cb0d05b7b02beca171e5365'),
    'src/content/knowledge/forensic-mobile-apps.md': (
        '77d36f4fc4b7ddaca1d300fa2f55770c3b03e59f3eb714ba54d5cd0b1dfb551e',
        'f942a8920d26b46f211db1a9bc38ad9ffe48cf7453a639e2cf548c95c8f0d591'),
    'src/content-curation/forensic-network-traffic.md': (
        'd0e53d957d0ed5a99f138107fa1abf9409f16456bfc2098ec39afe18b15a0d0c',
        '78f9e0effa178e1212d5132d1997b96bd44bc5570b978dd4c980629d1451f902'),
    'src/content/knowledge/forensic-network-traffic.md': (
        'e18655f78313c3b57e65ba67b0586af0f349a543a90a6e8c83b6e0a3c6788224',
        '00958704601b2fe5df7e8b25d0fdf73f9e30e738ec69b747e7f611b2a6ba40a9'),
    'src/content-curation/forensic-protected-data.md': (
        '01859c8f9656c4317110268ee877dcc453aa1f7fad3eb169f8997fb63046c67c',
        'da592cd7ac352d884b4cd264a988d536edfa91053d38f4adb847dc956dc1fd87'),
    'src/content/knowledge/forensic-protected-data.md': (
        '0c81f441f32b069872aecf82f2d617d43d9d1b2bae02ab8b49c31219fde8b193',
        '0a440893797dbf6fd6d32889ecd87c22b6da3e4e38f3f15bce9d4793b05b62a6'),
    'src/content-curation/forensic-registry.md': (
        '792128c77e00cad35477319b1d3be93a9bd09e54e98b423b57b417428a7f968c',
        'd5e21f8e8a0d5534598624c6544b684b6acd2ac92941b3f5dc72beabaeaac539'),
    'src/content/knowledge/forensic-registry.md': (
        'bbc2df499075f1f885cf083fb7192e61e3a7a5a2049d585fd9773bf4b22325d4',
        'fb08dda209d64ce39f937053ddb9a5c78062819980aa3b9d7b6a1f46834b7781'),
    'src/content-curation/forensic-remote-connections.md': (
        '13011284863ec6442dc98d31e8ffaa4654d8e4d581998874b5edac2db30bc13a',
        'eae4afd57424035a42d68426a2461032137a42876b36547ff3780a9b209e72d2'),
    'src/content/knowledge/forensic-remote-connections.md': (
        'ec7e4e6e5d310937bae20658f090422ec0a4dc0319a885cf4285e0973a03d8c8',
        'fbd9dabd6dddc81b8e480e1ee93663c9ec4acfe2772526d8a19aec7f875503fe'),
    'src/content-curation/forensic-usb-evidence.md': (
        'f534b92e74d9cce0c7a8a5c07567675f35f74e745ec43ec4ea9264c8754e32f6',
        'c62ae011134cade98b9be25da8ffda3de0ae713c7e6dfa6a490f1c057557af00'),
    'src/content/knowledge/forensic-usb-evidence.md': (
        '8dfd3dd1df3c8eeed8574b4467d733a6e9e823badd7bba2bf880b48f7730b0cc',
        'a810bc669d851f2c54ae8f32cffbc4a8ebe4cbc418df0ca22da8ce44f773e2d8'),
    'src/content-curation/forensic-windows-logs.md': (
        'b9953260551f9603f48516c5789d7cfe09e990e22a3ed8228bd1674cc203474f',
        'e43f5bf38c241e7ee6c2714870228f5bc50dc23e1543e3001f1734f3cd570f17'),
    'src/content/knowledge/forensic-windows-logs.md': (
        'b3a9910c71b35442132c8f08d7b087dba9738a9ef199f588a0b61afdd9a1bde4',
        '1b7204b25b3d4c5e7175827acd4027e7bd3c87ac6ab9dd89f9e1bae01c04894c'),
    'src/content-curation/forensic-server-panel.md': (
        '69cf649c53dce161f481d0603b799f2cc1bd285019535255b0b715b4fb8ae71f',
        'd713d37a4285f9daffa86d735e3fd8c08dc8187685b0eed20ee7c50eced29a09'),
    'src/content/knowledge/forensic-server-panel.md': (
        '6b0d8fc410f78c6088b69cc6b6a1eb4466b0c86c2760d92bb4d2603efe617256',
        '4278d1c8833f5c3b2a28f2e84b2ba02c6c6242b88ed3ee055c56bc226f4e0f0f'),
    'src/content-curation/forensic-website-reconstruction.md': (
        '6cf0130eea80ae610239969683f01f6e16f6dfc0836c32066c43578b14350c68',
        '4ed5f5e116d57a151d98282602d78aa08f0dc2c89d2591638f01b02c05d446c5'),
    'src/content/knowledge/forensic-website-reconstruction.md': (
        '7478266ead31f956775db1fe2b54fc702847d22e35866062dbdc5a5c3d6a6e2a',
        '1ca999d085a96b963262fc4c6b5876464dec4abd0facf85ef4039ab9e05467fc'),
    'src/content-curation/fic-case-04.md': (
        '8abe6143ac3aa726442c9f7e0d30b072f312e48a2d39eda89023a86f84013803',
        'a16f631328b66ef392109739bec91c8bc54b2939fd76fdd5f7b516d7799cd203'),
    'src/content/knowledge/fic-case-04.md': (
        'efb0214df12c3dacb76323c8a3d4923134626fa249294262315d215c83cee2a5',
        'f4656c552bd2cc8877b96eeb26941e8debdcf810c2fc9f15ef47cfade4d062fe'),
    'src/content-curation/forensic-server-services.md': (
        '1113215e5b11cffd4bb1247935805ab94c60dc889d1cbc0ba980312fecab8516',
        '6e96baeaca27e40ee970a55037ccc50bef84a7a75fbc05955f5cfa1f98096d08'),
    'src/content-curation/fic-case-03.md': (
        '2363c3037a674dd69225f2306f0ff59c6501def1c0e58a92f0d0ec3d7e397f3b',
        'fe997c7db8f47ab2890534c434d6667c9e5bc28b01d30018123c1396a650c4b3'),
    'src/content-curation/forensic-guide-server.md': (
        '473647aa81725ae40e9ccc1ea65aaf8565c6952f43eef059abdf50796f688bf6',
        'fe12d22d6c785966949244709a7fc5370ffc9bb8c534f884af881c54f83f8e94'),
    'src/content/knowledge/forensic-server-services.md': (
        '6a1ac386209c80cf057609166b884d2a12311c6d3f138117c2a527acbe0a5867',
        '7d0a851532c2db66d3c1782c0a1bf3e09b92669b97494106f9d4d1019d6cbed3'),
    'src/content/knowledge/fic-case-03.md': (
        '012b2aa77087d8d68cd2cf33aee8c76677e1641150293a8829dca11ba247afd4',
        'e62c11b0ef2b6ae4b8946f2730cc31a885be6a36e89e900a460c7699b091c667'),
    'src/content/knowledge/forensic-guide-server.md': (
        '8ed138abbe49466820a50720ce082b3bf0ce4a2f25eceb0613797124f7c92781',
        'e517f94a32bc1093b4cf84af0befbdc81e5418285c4103027520bda1008cc0c3'),
    'src/content-curation/docker-evidence-01.md': (
        '263e92129b932a3369fffe42f9fa9921799e4320f4df6f5c521850be75dc5c11',
        '527afd4f18f29afc44ef502ce218bc4ba31c024effbc6f5a3bcb4d271170b1cf'),
    'src/content/knowledge/docker-evidence-01.md': (
        'b9a2f55a60b8a1d5895c70489b6e351a7c4b7aab00aafc5013198e20a6dc47db',
        'a982292541887e0ab186f70c98b919789212484abd604bb39c0485975279bde9'),
    'src/content-curation/docker-evidence-02.md': (
        '4553e5d8bba70c932bed559780acbf40f8bf7590f4f0fabbacd286fbfd3f468f',
        'f109d518dae518ac5833a52b19fe70af7d898d576629c4e095e0392095bc87b7'),
    'src/content/knowledge/docker-evidence-02.md': (
        '63cc7d8935c12247a679cee56cf3fde1a6d0a550c84320fe019bc5d76d711a67',
        'c9eb26c2fe58e208d1291ebc949cdd2448d78252d0618019852f26ba215c0e1b'),
    'src/content-curation/docker-evidence-03.md': (
        '4883ba75506d3e65e375a013c3e6fe3920436818d614ecaf741d20fe7a978b57',
        '6bf2b18d4371ae0abea9b8ca724b1d50e145c0d8ba6dc40ee65ddf7f7297b5c8'),
    'src/content/knowledge/docker-evidence-03.md': (
        '4aaecb3c4f371798516aa21441df53a9d04d51aba94ddea9c2ba7376c10c9545',
        '6896598610120b157f5334022dfde94e9d53b4c58bce7cde4ef7a4d843dd7cca'),
    'src/content-curation/docker-evidence-04.md': (
        '0489405469e4f99f2955195c952917eeb59b09d0315633a9d113134e06881048',
        '4af886f27b99505047e1ea74388b903d00d639c8772d738324f6f335157d6717'),
    'src/content/knowledge/docker-evidence-04.md': (
        '9c89e8e9fea619b624f30c8cdfdbf2f17fbe1dd50c0d4023ce1b5f6bfcaf7d2d',
        '4da8306af3d19bd96f1b59a3f0d7fd72773560223959a304802b1fb978f98c54'),
    'src/content-curation/docker-evidence-05.md': (
        'e0e573ad739803a0c2dcb2fa9096adcf0285d0dc17b79943d8fa4ea5b66fa7d5',
        'c1ae9b809d2924639e20d66e28419b4f5bd31ee0504134baf1b4b07226d4b947'),
    'src/content/knowledge/docker-evidence-05.md': (
        'e22a9169430288e4602c477372a20f205029fd401eac269447429c3dd261524a',
        'f27cb05cfa98d08e0639837099cea5c7ff92315a0a630047d65a5b0eeb215b6f'),
    'src/content-curation/fic-case-05.md': (
        'b08cbdbb2f080c50af46b228c72165c0759ace59c2dc92454314e76b91ce3ecf',
        '7ef028074426918d4f2c0a826fbb920ef6b34744c7ccc856a5e0d02fbd3649af'),
    'src/content/knowledge/fic-case-05.md': (
        '96db0385b493abd28fc1a7e3953e1403e0f73eabcbc6c6667995cd9499595354',
        '14a02315732c72be31daa419f18dd50851c169f4b859872632e2804a5f5e0de3'),
    'src/content-curation/forensic-cloud-vm.md': (
        '3ab293acccf85e99d58e4f4db3d2e6e32c49eb30eca27f54064137494d086c64',
        'fd550dd1a6b5d03e9a0823d2e9363f85142718c1d0d27aa3b0597813762e05b0'),
    'src/content/knowledge/forensic-cloud-vm.md': (
        '28a26f48d120cac86e664c07bbd5d869b0c23be4bae424b0974ff96d10469069',
        'ab7ea3fb84cb5487de1c3f29a7301604cc0b5b41139c2fc49f2573f1b344c29d'),
    'src/content-curation/forensic-database-recovery.md': (
        '4da563ba374bfe016ddb40436dd74198a9a9a67fa0a6206718d93ae75340a0c3',
        'b4ac7b9d7054520f3e2f5241306e0dfe5fb626dd63fa09044af5af1e794ea182'),
    'src/content/knowledge/forensic-database-recovery.md': (
        'aae9aef7e11a5b05913e8b3555ab5e284c86f4c4004ced1964a2f7dc790c098e',
        'ea261a9ff77d5ac06cbad66f0134f2d960ea36dec0bc2bcbe4b1f9c8a76a7e67'),
    'src/content-curation/forensic-kubernetes-cluster.md': (
        '7ca27946f56166d11333e2a49caba89e1aa257056a76b99f17d27e232b334569',
        'd98165dfb1cd423df04196a4e7ae017c5fb0bb4cd37e6538a7b460edd053c29f'),
    'src/content/knowledge/forensic-kubernetes-cluster.md': (
        '818c6ce180d250b6bfde6310adaf82e825f252e3a87930b88a25c9edecf6bc69',
        '2b21bf01f59dd7b001bef255dd0aa64e38f11f96300c9a11f3df47c70c571e33'),
    'src/content-curation/git-docker-03.md': (
        '2ee0d60e56716a38a7a02a18fc257f4e3d3ea074996fead2caa7465c451b625f',
        'a0c1b01394d4bde1e6e43e0995a418d20a64ed5b9562655b5aa489856b59ef92'),
    'src/content/knowledge/git-docker-03.md': (
        '0969078999adb4b51720870e4db54470f66339f61bd3a009c408e39c5cfb3a3d',
        '81321180d0bb63ade59960023c9c52357872355489f3519b6a8d5dc4c18fff54'),
    'src/content-curation/git-docker-04.md': (
        'eb92f1b4923b4101ce680e89f52fe8be5bb1159f7f5c9e204a8d9e88559869c0',
        '85ca63106be07965075daee9e6daa7ba6a470da68173f06129359f0b30df1cc2'),
    'src/content/knowledge/git-docker-04.md': (
        '8f56bb5b8208b27ded8d1c7d8c71aaeb537ed45b5d472448a78d79f48b69019c',
        'd375e23f1f560d365466d2caf6d92ec464956804f4d74daf73c7cae496d57781'),
    'src/content-curation/git-docker-05.md': (
        'd4a0a2eaf0f3841b79daf90e384e3a144c75c9dfe39f7a0bf6bbd66f173e7613',
        'dadfc4af16ba35e0245dcbf668ff1cbd7033f6b9817c0a774dabdb7a527df787'),
    'src/content/knowledge/git-docker-05.md': (
        '2e6a8ca9e10c2346539d1c4ff68b915a7ce4fe69e352c1f8a4f21e8af323e26e',
        '9c88cc3afee6355ff7f32603a7ea982fd4d31b0c82c9b231374b6194bfdbbe39'),
    'src/content-curation/git-docker-06.md': (
        '746c32ccfecb84d7140b99d8cb9ea037317e4e01c35f0b85ef7098d5fba83906',
        'a16bccfa6a57b24daea3f39e02f99145841027d9b3c8e7edee60c81eff448cab'),
    'src/content/knowledge/git-docker-06.md': (
        '2a578bc67971a906fa006c660802cf1b27db5053730e8ac3827e63fa4f750bfa',
        '5a4e2edb90af37ca7c3a7dd4def093c7668228989bede8e58244fbbc2361d8e4'),
    'src/content-curation/git-docker-07.md': (
        '8cebd67dec4f6593b988cbaf95d92c2b747a84252569da16b49ca53b9ae8e19b',
        '8067ae691d0438158170b472ef93dedfca737edd264f611e684d007df1cc42a0'),
    'src/content/knowledge/git-docker-07.md': (
        '3ffbb751210ce90d465e67374f4ac58d475824b0f40e07fbc87d6946686c0148',
        '063a172d05510f6c16f0a1a858ffb9535497cd63199c97fc2f68e0111afb4fd0'),
    'src/content-curation/git-docker-08.md': (
        'f0eb93917e3cabc254fb83ed37cde259efd4ae7f9b4d8ea6d77324c30a2cbb5a',
        '2123ebcff53d6b142f4aa38b6aa0379aa14d992057fbb63f03b93b6191be9211'),
    'src/content/knowledge/git-docker-08.md': (
        '1eb23275ab9803dadee5c0cc208dc6ad182a083012c6a2bc392ab16e2efe26d5',
        'c90b7a005f266924761858bdce186f7a83afca41bafb25b4b2af42dbe193672a'),
}




# Explicit review of database-recovery sections 01-11; original commands/tables retained.
APPROVED_PREFIX_TRANSITIONS = {'src/content-curation/forensic-database-recovery.md': ((26419, '77a63794767a7884ba220d5ba802b4ecb27697e0b079bfce617132d352866e54'), (27211, '7a9ca83530322a4bb7d3b7e9e42575cf6b933fbb7bd228482ef449af3ecef441'))}

def reviewed_preservation_prefix(path, size, historical_hash):
    transition = APPROVED_PREFIX_TRANSITIONS.get(path)
    if transition and transition[0] == (size, historical_hash):
        return transition[1]
    return size, historical_hash


def reviewed_preservation_hash(path, historical_hash):
    transition = APPROVED_TRANSITIONS.get(path)
    if transition and transition[0] == historical_hash:
        return transition[1]
    return historical_hash


class BaotaBindingContentTests(unittest.TestCase):
    def body(self):
        text = (ROOT / f'src/content-curation/{ID}.md').read_text('utf-8')
        self.assertIn('## 10 宝塔绕过绑定手机号：离线仿真实战', text)
        return text.split('## 10 宝塔绕过绑定手机号：离线仿真实战', 1)[1]

    def blocks(self, language='bash'):
        return re.findall(r'(?ms)^```' + language + r'\n(.*?)^```\s*$', self.body())

    def shell(self, marker):
        matches = [b for b in self.blocks() if marker in b]
        self.assertEqual(len(matches), 1, marker)
        return matches[0]

    def python_block(self, marker):
        matches = [b for b in self.blocks('python') if marker in b]
        for b in self.blocks():
            for code in re.findall(r"(?ms)^python3[^\n]* <<'PY'\n(.*?)^PY\s*$", b):
                if marker in code:
                    matches.append(code)
        self.assertEqual(len(matches), 1, marker)
        return matches[0]

    def run_python(self, code, *args):
        return subprocess.run([sys.executable, '-X', 'utf8', '-', *map(str, args)], input=code,
                              capture_output=True, text=True, encoding='utf-8')

    def bash(self):
        candidates = [shutil.which('bash'), r'C:\Program Files\Git\bin\bash.exe']
        for candidate in candidates:
            if candidate and Path(candidate).is_file():
                return candidate
        self.skipTest('Bash is required for Linux shell examples')

    def posix(self, path):
        value = str(path).replace('\\', '/')
        if re.match(r'^[A-Za-z]:/', value):
            return '/' + value[0].lower() + value[2:]
        return value

    def test_methods_are_distinct_and_original_sections_remain(self):
        text = (ROOT / f'src/content-curation/{ID}.md').read_text('utf-8')
        self.body()
        sections = re.findall(r'(?m)^## (\d+) ', text)
        self.assertEqual(list(map(int, sections)), list(range(1, 11)))
        for token in ('302', '/files', 'show_force_bind', 'bind.pl', 'is_bind', 'userInfo.json',
                      'get_cloud_list', 'initBind.pl', 'aaPanel', 'BasicAuth', '验证码'):
            self.assertIn(token, self.body())

    def test_frontend_patch_handles_both_ascii_quote_styles(self):
        code = self.python_block('FORENSIC_OFFLINE')
        with tempfile.TemporaryDirectory() as td:
            js = Path(td) / 'index.js'
            for quote in ("'", '"'):
                original = f"if (bind_user == {quote}True{quote}) {{ show_force_bind(); }}\n"
                js.write_text(original, 'utf-8')
                result = self.run_python(code, js)
                self.assertEqual(result.returncode, 0, result.stderr)
                patched = js.read_text('utf-8')
                node = shutil.which('node')
                if node:
                    harness = 'let bind_user="True";let calls=0;function show_force_bind(){calls++;}\n'
                    before = subprocess.run([node, '-e', harness + original + 'console.log(calls)'], capture_output=True, text=True)
                    after = subprocess.run([node, '-e', harness + patched + 'console.log(calls)'], capture_output=True, text=True)
                    self.assertEqual((before.returncode, before.stdout.strip()), (0, '1'))
                    self.assertEqual((after.returncode, after.stdout.strip()), (0, '0'))

    def test_frontend_patch_stops_before_writing_on_wrong_match_count(self):
        code = self.python_block('FORENSIC_OFFLINE')
        with tempfile.TemporaryDirectory() as td:
            js = Path(td) / 'index.js'
            for value in ('// no binding check\n', "if(bind_user == 'True'){}\n" * 2):
                js.write_text(value, 'utf-8')
                original = js.read_bytes()
                self.assertNotEqual(self.run_python(code, js).returncode, 0)
                self.assertEqual(js.read_bytes(), original)

    def test_local_user_info_is_json_and_existing_evidence_is_preserved(self):
        code = self.python_block('offline-demo')
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'userInfo.json'
            result = self.run_python(code, target)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(target.read_text('utf-8'))
            self.assertEqual(data['uid'], 1)
            self.assertEqual(data['username'], 'offline-demo')
            self.assertEqual(data['access_key'], '')
            self.assertEqual(set(data), {'id', 'uid', 'state', 'username', 'secret_key', 'access_key',
                                         'address', 'addtime', 'idc_code', 'area', 'serverid', 'ukey'})
            self.assertEqual((data['id'], data['state'], data['addtime']), (1, 1, 1))
            before = target.read_bytes()
            self.assertNotEqual(self.run_python(code, target).returncode, 0)
            self.assertEqual(before, target.read_bytes())

    def test_is_bind_patch_changes_only_binding_and_restores_original_behavior(self):
        code = self.python_block('local binding gate only')
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'public.py'
            original = b"def is_bind():\n    return False\n\ndef panel_login():\n    return False\n"
            target.write_bytes(original)
            namespace = {}
            exec(compile(original, '<fixture-baseline>', 'exec'), namespace)
            self.assertEqual((namespace['is_bind'](), namespace['panel_login']()), (False, False))
            result = self.run_python(code, target)
            self.assertEqual(result.returncode, 0, result.stderr)
            namespace = {}
            exec(compile(target.read_bytes(), '<fixture-modified>', 'exec'), namespace)
            self.assertEqual((namespace['is_bind'](), namespace['panel_login']()), (True, False))
            target.write_bytes(original)
            namespace = {}
            exec(compile(target.read_bytes(), '<fixture-rollback>', 'exec'), namespace)
            self.assertEqual((namespace['is_bind'](), namespace['panel_login']()), (False, False))

    def test_is_bind_patch_preserves_file_on_ambiguous_definition_or_signature(self):
        code = self.python_block('local binding gate only')
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'public.py'
            for raw in (b'def other():\n    return False\n',
                        b'def is_bind():\n    return False\ndef is_bind():\n    return False\n',
                        b'def is_bind(user):\n    return False\n'):
                target.write_bytes(raw)
                self.assertNotEqual(self.run_python(code, target).returncode, 0)
                self.assertEqual(target.read_bytes(), raw)

    def test_offline_list_defaults_preserve_existing_values_and_non_dict_errors(self):
        code = self.python_block("softList.setdefault('pro', -1)")
        class PanelError(Exception):
            pass
        class Public:
            pass
        public = Public()
        public.PanelError = PanelError
        for source in ({'msg': 'offline'}, {'msg': 'offline', 'pro': 123, 'ltd': 456},
                       {'list': [{'name': 'local'}], 'pro': 123, 'ltd': 456}):
            namespace = {'softList': source.copy(), 'public': public}
            exec(compile(code, '<documented-offline-list>', 'exec'), namespace)
            result = namespace['softList']
            self.assertEqual(result['pro'], source.get('pro', -1))
            self.assertEqual(result['ltd'], source.get('ltd', -1))
            self.assertEqual(result['list'], source.get('list', []))
        with self.assertRaises(PanelError):
            exec(compile(code, '<documented-offline-list>', 'exec'), {'softList': None, 'public': public})

    def test_shell_and_python_examples_parse(self):
        for block in self.blocks():
            result = subprocess.run([self.bash(), '-n'], input=block, capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stderr)
        ast.parse(self.python_block('FORENSIC_OFFLINE'))
        ast.parse(self.python_block('offline-demo'))
        ast.parse(self.python_block('local binding gate only'))
        ast.parse(self.python_block("softList.setdefault('pro', -1)"))

    def test_backup_and_restore_recover_present_and_absent_file_states(self):
        backup = self.shell('Baseline saved:')
        restore = self.shell('(cd "$PANEL" && sha256sum -c')
        # Run the file restoration part; the final restart is a separate operator step.
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            panel, saved = base / 'panel', base / 'saved'
            present = ('BTPanel/static/js/index.js', 'BTPanel/__init__.py', 'class/public.py',
                       'class/panelPlugin.py', 'data/bind.pl')
            contents = {}
            for rel in present:
                p = panel / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                contents[rel] = ('original:' + rel + '\n').encode()
                p.write_bytes(contents[rel])
            env = os.environ.copy()
            env.update(PANEL=self.posix(panel), SAVE=self.posix(saved), LANG='C.UTF-8')
            result = subprocess.run([self.bash(), '-c', backup], env=env, capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stderr)
            for rel in present:
                (panel / rel).write_bytes(b'changed\n')
            (panel / 'data/userInfo.json').write_text('{"uid":1}', 'utf-8')
            (panel / 'data/initBind.pl').write_text('True', 'utf-8')
            result = subprocess.run([self.bash(), '-c', restore], env=env, capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stderr)
            for rel, value in contents.items():
                self.assertEqual((panel / rel).read_bytes(), value)
            self.assertFalse((panel / 'data/userInfo.json').exists())
            self.assertFalse((panel / 'data/initBind.pl').exists())

    def test_maintained_body_survives_curation_twice(self):
        import import_manuals
        self.body()
        original = (ROOT / f'src/content/knowledge/{ID}.md').read_text('utf-8')
        with tempfile.TemporaryDirectory() as td:
            notes, guides = Path(td) / 'notes', Path(td) / 'guides'
            notes.mkdir(); guides.mkdir()
            note = notes / f'{ID}.md'
            note.write_text(original.split('---', 2)[0] + '---' + original.split('---', 2)[1] + '---\n\n旧正文\n', 'utf-8')
            shutil.copy2(ROOT / f'src/content-curation/{ID}.md', guides / note.name)
            with patch.object(import_manuals, 'NOTES', notes), patch.object(import_manuals, 'CURATION', guides):
                import_manuals.apply_forensics_curation()
                after = note.read_bytes()
                import_manuals.apply_forensics_curation()
                self.assertEqual(note.read_bytes(), after)
                self.assertIn('## 10 宝塔绕过绑定手机号', note.read_text('utf-8'))
                self.assertIn('track: 服务器取证', note.read_text('utf-8'))

    def test_source_links_are_internal_and_reconstruction_links_to_one_body(self):
        body = self.body()
        registry = json.loads((ROOT / 'src/data/forensics-supplements.json').read_text('utf-8'))
        by_url = {row['url']: row for row in registry['webSources']}
        for url in ('https://www.cnblogs.com/WXjzc/p/17738053.html',
                    'https://blog.csdn.net/lqplyx518/article/details/130460126'):
            self.assertTrue(url in by_url, url)
            self.assertIn(ID, by_url[url]['articleIds'])
            self.assertNotIn(url, body)
        reconstruction = (ROOT / 'src/content-curation/forensic-website-reconstruction.md').read_text('utf-8')
        self.assertIn('面板账号不是商城后台账号', reconstruction)
        self.assertIn('## 01 PHP：', reconstruction)

    def test_acceptance_distinguishes_ui_cloud_data_and_historical_identity(self):
        body = self.body()
        for token in ('空列表', '未开通', '历史绑定', '服务端', '回滚', '构造', '面板服务'):
            self.assertIn(token, body)

    def test_screenshot_material_is_integrated_without_dns_or_upgrade_confusion(self):
        body = self.body()
        for token in ('7.7.0', '7.8.0', 'LinuxPanel-7.7.0.zip', 'LinuxPanel-8.0.0.zip',
                      'scp -P 2222', 'bash update.sh', '完整快照回滚',
                      'DNS/BIND', '现有数据库文件', 'WAL', 'sites', 'databases'):
            self.assertIn(token, body)

    def test_documented_database_queries_run_read_only_on_a_constructed_schema(self):
        sql = self.blocks('sql')
        self.assertEqual(len(sql), 1)
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / 'snapshot.db'
            with sqlite3.connect(db) as connection:
                connection.executescript('''
                CREATE TABLE users(id INTEGER, username TEXT, login_ip TEXT, login_time INTEGER);
                CREATE TABLE sites(id INTEGER, name TEXT, path TEXT, status INTEGER);
                CREATE TABLE databases(id INTEGER, name TEXT, username TEXT, accept TEXT, db_type TEXT);
                INSERT INTO users VALUES(1, 'analyst-demo', '192.0.2.10', 1);
                INSERT INTO sites VALUES(1, 'site.example', '/www/wwwroot/site-a', 1);
                INSERT INTO databases VALUES(1, 'app_db', 'app_user', '127.0.0.1', 'mysql');
                ''')
            connection.close()
            before = db.read_bytes()
            connection = sqlite3.connect(db.as_uri() + '?mode=ro', uri=True)
            rows = [connection.execute(statement).fetchall() for statement in sql[0].split(';') if statement.strip()]
            connection.close()
            self.assertEqual([len(row) for row in rows], [1, 1, 1])
            self.assertEqual(rows[1][0][1], 'site.example')
            self.assertEqual(db.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
