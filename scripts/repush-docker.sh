#!/bin/bash
set -e

TARGET_REGISTRY="test.push"

if [ -z "$1" ]; then
    echo "사용법: $0 <tar_file>"
    exit 1
fi

TAR_FILE="$1"

if [ ! -f "$TAR_FILE" ]; then
    echo "오류: 파일을 찾을 수 없습니다: $TAR_FILE"
    exit 1
fi

# 파일명에서 .tar 제거 후 __ 기준으로 분리
filename=$(basename "$TAR_FILE" .tar)
IFS='__' read -ra parts <<< "$filename"
len=${#parts[@]}

# 마지막 2개는 항상 tag와 arch
arch="${parts[$len-1]}"
tag="${parts[$len-2]}"

# 나머지 토큰으로 registry/namespace/image 결정
if [ $len -eq 3 ]; then
    # image__tag__arch → docker.io/library/image:tag
    registry="docker.io"
    namespace="library"
    image="${parts[0]}"
elif [ $len -eq 4 ]; then
    # 첫 번째 토큰에 점이 있으면 registry, 없으면 namespace
    if [[ "${parts[0]}" == *.* ]]; then
        # registry__image__tag__arch → registry/library/image:tag
        registry="${parts[0]}"
        namespace="library"
        image="${parts[1]}"
    else
        # namespace__image__tag__arch → docker.io/namespace/image:tag
        registry="docker.io"
        namespace="${parts[0]}"
        image="${parts[1]}"
    fi
else
    # registry__namespace__image__tag__arch (5개 이상)
    registry="${parts[0]}"
    namespace="${parts[1]}"
    # 나머지는 image (3번째부터 끝-2까지)
    image="${parts[2]}"
    for ((i=3; i<$len-2; i++)); do
        image="${image}_${parts[$i]}"
    done
fi

original_ref="$registry/$namespace/$image:$tag"
new_ref="$TARGET_REGISTRY/$namespace/$image:$tag"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "원본: $original_ref"
echo "변경: $new_ref"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "[1/3] Loading image..."
docker load -i "$TAR_FILE"
echo ""

echo "[2/3] Tagging image..."
docker tag "$original_ref" "$new_ref"
echo ""

echo "[3/3] Pushing to registry..."
docker push "$new_ref"
echo ""

echo "✓ 완료: $new_ref"
